from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import uvicorn
import os
import asyncio
from contextlib import asynccontextmanager

# Import our Weaviate service
from weaviate_k8_test import WeaviateService, DEFAULT_SAMPLE_PRODUCTS

class ProductModel(BaseModel):
    """
    Pydantic model for product validation with comprehensive schema
    Ensures data integrity before insertion into Weaviate
    """
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., min_length=1, description="Product name")
    description: str = Field(..., min_length=1, description="Product description")
    category: str = Field(..., description="Product category")
    price: float = Field(..., gt=0, description="Product price in USD")
    brand: str = Field(..., description="Product brand")
    tags: List[str] = Field(default=[], description="Product tags")

class SearchRequest(BaseModel):
    """
    Request model for search operations with validation
    """
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: Optional[int] = Field(default=5, ge=1, le=50, description="Number of results to return")
    alpha: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Hybrid search balance")

class SearchResponse(BaseModel):
    """
    Standardized response model for all search operations
    """
    success: bool
    results: List[Dict[str, Any]]
    query: str
    search_type: str
    total_results: int
    message: Optional[str] = None

# Global service instance - will be initialized in lifespan
weaviate_service: Optional[WeaviateService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for proper resource initialization and cleanup
    Ensures Weaviate connection is established at startup and closed at shutdown
    """
    global weaviate_service
    
    try:
        # Startup: Initialize Weaviate service
        print("🚀 Starting Weaviate Web Service...")
        weaviate_service = WeaviateService()
        weaviate_service.connect()
        
        # Ensure collection exists
        if weaviate_service.create_collection():
            print("📦 Collection ready for operations")
        
        yield  # Application runs here
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise
    finally:
        # Shutdown: Clean up resources
        if weaviate_service:
            weaviate_service.close()
        print("🔌 Weaviate Web Service shut down")

# Initialize FastAPI app with proper configuration
app = FastAPI(
    title="Weaviate Search API",
    description="Advanced search API powered by Weaviate vector database with multiple search modes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint for monitoring"""
    return {"status": "healthy", "service": "weaviate-search-api"}

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serve the main HTML interface with tabbed search functionality
    Modern responsive design with error handling and loading states
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weaviate Search Interface</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
            }
            
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
                font-size: 2.5em;
                font-weight: 300;
            }
            
            .search-section {
                margin-bottom: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #dee2e6;
            }
            
            .search-input {
                width: 100%;
                padding: 15px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-bottom: 15px;
                transition: border-color 0.3s ease;
            }
            
            .search-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .tabs {
                display: flex;
                background: #fff;
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .tab {
                flex: 1;
                padding: 15px 20px;
                background: #f8f9fa;
                border: none;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
                color: #666;
            }
            
            .tab.active {
                background: #667eea;
                color: white;
            }
            
            .tab:hover:not(.active) {
                background: #e9ecef;
                color: #333;
            }
            
            .search-btn {
                width: 100%;
                padding: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease;
            }
            
            .search-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
            }
            
            .search-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .results {
                margin-top: 30px;
            }
            
            .result-item {
                background: #fff;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 10px;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
                border-left: 4px solid #667eea;
                transition: transform 0.2s ease;
            }
            
            .result-item:hover {
                transform: translateX(5px);
            }
            
            .product-name {
                font-size: 1.3em;
                font-weight: 600;
                color: #333;
                margin-bottom: 8px;
            }
            
            .product-details {
                color: #666;
                margin-bottom: 10px;
                line-height: 1.5;
            }
            
            .product-meta {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 15px;
                padding-top: 10px;
                border-top: 1px solid #eee;
            }
            
            .price {
                font-size: 1.2em;
                font-weight: 600;
                color: #28a745;
            }
            
            .score {
                font-size: 0.9em;
                color: #666;
                background: #f8f9fa;
                padding: 4px 8px;
                border-radius: 15px;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
            }
            
            .error {
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #f5c6cb;
                margin-top: 20px;
            }
            
            .data-management {
                margin-bottom: 30px;
                padding: 20px;
                background: #e8f5e8;
                border-radius: 10px;
                border: 1px solid #d4edda;
            }
            
            .file-upload {
                margin-bottom: 15px;
            }
            
            .file-input {
                width: 100%;
                padding: 10px;
                border: 2px dashed #ccc;
                border-radius: 8px;
                background: #f8f9fa;
            }
            
            .upload-btn, .load-sample-btn {
                padding: 10px 20px;
                margin: 5px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: 500;
                transition: background-color 0.3s ease;
            }
            
            .upload-btn {
                background: #28a745;
                color: white;
            }
            
            .upload-btn:hover {
                background: #218838;
            }
            
            .load-sample-btn {
                background: #17a2b8;
                color: white;
            }
            
            .load-sample-btn:hover {
                background: #138496;
            }
            
            .advanced-options {
                margin-top: 15px;
                padding: 15px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            
            .option-row {
                display: flex;
                gap: 15px;
                margin-bottom: 10px;
            }
            
            .option-group {
                flex: 1;
            }
            
            label {
                display: block;
                font-weight: 500;
                margin-bottom: 5px;
                color: #333;
            }
            
            input[type="range"], input[type="number"] {
                width: 100%;
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            .range-value {
                color: #667eea;
                font-weight: 600;
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Weaviate Search Interface</h1>
            
            <!-- Data Management Section -->
            <div class="data-management">
                <h3>📦 Data Management</h3>
                <div class="file-upload">
                    <input type="file" id="fileInput" accept=".json" class="file-input" multiple>
                    <button class="upload-btn" onclick="uploadData()">Upload Products</button>
                    <button class="load-sample-btn" onclick="loadSampleData()">Load Sample Data</button>
                </div>
                <div id="uploadStatus"></div>
            </div>
            
            <!-- Search Interface -->
            <div class="search-section">
                <input type="text" id="searchQuery" class="search-input" placeholder="Enter your search query..." />
                
                <!-- Search Type Tabs -->
                <div class="tabs">
                    <button class="tab active" onclick="setSearchType('hybrid')">🔀 Hybrid Search</button>
                    <button class="tab" onclick="setSearchType('vector')">🧠 Vector Search</button>
                    <button class="tab" onclick="setSearchType('keyword')">📝 Keyword Search</button>
                    <button class="tab" onclick="setSearchType('rag')">🤖 RAG Search</button>
                </div>
                
                <!-- Advanced Options -->
                <div class="advanced-options" id="advancedOptions">
                    <div class="option-row">
                        <div class="option-group">
                            <label for="limitInput">Results Limit:</label>
                            <input type="number" id="limitInput" min="1" max="50" value="5">
                        </div>
                        <div class="option-group" id="alphaGroup">
                            <label for="alphaInput">Alpha (Vector ← → Keyword):</label>
                            <input type="range" id="alphaInput" min="0" max="1" step="0.1" value="0.5" oninput="updateAlphaValue()">
                            <span class="range-value" id="alphaValue">0.5</span>
                        </div>
                    </div>
                </div>
                
                <button class="search-btn" id="searchBtn" onclick="performSearch()">Search Products</button>
            </div>
            
            <!-- Results Section -->
            <div class="results" id="results"></div>
        </div>

        <script>
            let currentSearchType = 'hybrid';
            
            // Set search type and update UI
            function setSearchType(type) {
                currentSearchType = type;
                
                // Update active tab
                document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                event.target.classList.add('active');
                
                // Show/hide alpha control for hybrid search
                const alphaGroup = document.getElementById('alphaGroup');
                alphaGroup.style.display = type === 'hybrid' ? 'block' : 'none';
            }
            
            // Update alpha value display
            function updateAlphaValue() {
                const alphaInput = document.getElementById('alphaInput');
                const alphaValue = document.getElementById('alphaValue');
                alphaValue.textContent = alphaInput.value;
            }
            
            // Perform search based on current type
            async function performSearch() {
                const query = document.getElementById('searchQuery').value.trim();
                if (!query) {
                    alert('Please enter a search query');
                    return;
                }
                
                const limit = parseInt(document.getElementById('limitInput').value);
                const alpha = parseFloat(document.getElementById('alphaInput').value);
                
                const searchBtn = document.getElementById('searchBtn');
                const resultsDiv = document.getElementById('results');
                
                // Show loading state
                searchBtn.disabled = true;
                searchBtn.textContent = 'Searching...';
                resultsDiv.innerHTML = '<div class="loading">🔍 Searching products...</div>';
                
                try {
                    let url = `/search/${currentSearchType}`;
                    let body = { query, limit };
                    
                    if (currentSearchType === 'hybrid') {
                        body.alpha = alpha;
                    }
                    
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(body)
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        displayResults(data);
                    } else {
                        throw new Error(data.message || 'Search failed');
                    }
                    
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                    console.error('Search error:', error);
                } finally {
                    searchBtn.disabled = false;
                    searchBtn.textContent = 'Search Products';
                }
            }
            
            // Display search results
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                
                if (data.results.length === 0) {
                    resultsDiv.innerHTML = '<div class="loading">No results found for your query.</div>';
                    return;
                }
                
                let html = `<h3>📊 ${data.search_type.charAt(0).toUpperCase() + data.search_type.slice(1)} Search Results (${data.total_results} found)</h3>`;
                
                data.results.forEach((product, index) => {
                    let scoreDisplay = '';
                    if (product.score !== undefined) {
                        scoreDisplay = `<span class="score">Score: ${product.score.toFixed(4)}</span>`;
                    } else if (product.distance !== undefined) {
                        scoreDisplay = `<span class="score">Distance: ${product.distance.toFixed(4)}</span>`;
                    }
                    
                    let generatedContent = '';
                    if (product.generated_content) {
                        generatedContent = `<div style="margin-top: 10px; padding: 10px; background: #f0f8ff; border-radius: 5px; border-left: 3px solid #667eea;">
                            <strong>🤖 AI Generated:</strong> ${product.generated_content}
                        </div>`;
                    }
                    
                    html += `
                        <div class="result-item">
                            <div class="product-name">${product.name}</div>
                            <div class="product-details">
                                <strong>Category:</strong> ${product.category} | <strong>Brand:</strong> ${product.brand}<br>
                                <strong>Description:</strong> ${product.description}
                                ${product.tags && product.tags.length > 0 ? `<br><strong>Tags:</strong> ${product.tags.join(', ')}` : ''}
                            </div>
                            ${generatedContent}
                            <div class="product-meta">
                                <span class="price">${product.price.toFixed(2)}</span>
                                ${scoreDisplay}
                            </div>
                        </div>
                    `;
                });
                
                resultsDiv.innerHTML = html;
            }
            
            // Upload product data
            async function uploadData() {
                const fileInput = document.getElementById('fileInput');
                const files = fileInput.files;
                
                if (files.length === 0) {
                    alert('Please select JSON files to upload');
                    return;
                }
                
                const statusDiv = document.getElementById('uploadStatus');
                statusDiv.innerHTML = '<div class="loading">📤 Uploading products...</div>';
                
                try {
                    let allProducts = [];
                    
                    // Read all selected files
                    for (let file of files) {
                        const text = await file.text();
                        const products = JSON.parse(text);
                        
                        if (Array.isArray(products)) {
                            allProducts = allProducts.concat(products);
                        } else {
                            allProducts.push(products);
                        }
                    }
                    
                    const response = await fetch('/products', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(allProducts)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.innerHTML = `<div style="color: green;">✅ Successfully uploaded ${result.products_added} products!</div>`;
                        fileInput.value = ''; // Clear file input
                    } else {
                        throw new Error(result.message || 'Upload failed');
                    }
                    
                } catch (error) {
                    statusDiv.innerHTML = `<div class="error">❌ Upload error: ${error.message}</div>`;
                    console.error('Upload error:', error);
                }
            }
            
            // Load sample data
            async function loadSampleData() {
                const statusDiv = document.getElementById('uploadStatus');
                statusDiv.innerHTML = '<div class="loading">📦 Loading sample data...</div>';
                
                try {
                    const response = await fetch('/products/sample', {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.innerHTML = `<div style="color: green;">✅ Sample data loaded successfully! ${result.products_added} products added.</div>`;
                    } else {
                        throw new Error(result.message || 'Failed to load sample data');
                    }
                    
                } catch (error) {
                    statusDiv.innerHTML = `<div class="error">❌ Error loading sample data: ${error.message}</div>`;
                    console.error('Sample data error:', error);
                }
            }
            
            // Allow Enter key to trigger search
            document.getElementById('searchQuery').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Product management endpoints
@app.post("/products", response_model=Dict[str, Any])
async def add_products(products: List[ProductModel]):
    """
    Add multiple products to the Weaviate collection
    Validates each product against the schema before insertion
    """
    global weaviate_service
    
    if not weaviate_service:
        raise HTTPException(status_code=503, detail="Weaviate service not available")
    
    try:
        # Convert Pydantic models to dictionaries for Weaviate
        product_dicts = [product.model_dump() for product in products]
        
        success = weaviate_service.add_products(product_dicts)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully added {len(products)} products",
                "products_added": len(products)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add products to Weaviate")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding products: {str(e)}")

@app.post("/products/sample", response_model=Dict[str, Any])
async def load_sample_products():
    """
    Load the default sample products for testing purposes
    Useful for quick setup and demonstration
    """
    global weaviate_service
    
    if not weaviate_service:
        raise HTTPException(status_code=503, detail="Weaviate service not available")
    
    try:
        success = weaviate_service.add_products(DEFAULT_SAMPLE_PRODUCTS)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully loaded sample data",
                "products_added": len(DEFAULT_SAMPLE_PRODUCTS)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to load sample products")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading sample products: {str(e)}")

# Search endpoints for different search types
@app.post("/search/hybrid", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest):
    """
    Perform hybrid search combining vector similarity and keyword matching
    Alpha parameter controls the balance between vector (0.0) and keyword (1.0) search
    """
    global weaviate_service
    
    if not weaviate_service:
        raise HTTPException(status_code=503, detail="Weaviate service not available")
    
    try:
        results = weaviate_service.hybrid_search(
            query=request.query,
            limit=request.limit,
            alpha=request.alpha
        )
        
        return SearchResponse(
            success=True,
            results=results,
            query=request.query,
            search_type="hybrid",
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")

@app.post("/search/vector", response_model=SearchResponse)
async def vector_search(request: SearchRequest):
    """
    Perform pure vector similarity search using semantic embeddings
    Best for finding conceptually similar products
    """
    global weaviate_service
    
    if not weaviate_service:
        raise HTTPException(status_code=503, detail="Weaviate service not available")
    
    try:
        results = weaviate_service.vector_search(
            query=request.query,
            limit=request.limit
        )
        
        return SearchResponse(
            success=True,
            results=results,
            query=request.query,
            search_type="vector",
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search error: {str(e)}")

@app.post("/search/keyword", response_model=SearchResponse)
async def keyword_search(request: SearchRequest):
    """
    Perform BM25 keyword search for exact term matching
    Best for finding products with specific terms in name/description
    """
    global weaviate_service
    
    if not weaviate_service:
        raise HTTPException(status_code=503, detail="Weaviate service not available")
    
    try:
        results = weaviate_service.keyword_search(
            query=request.query,
            limit=request.limit
        )
        
        return SearchResponse(
            success=True,
            results=results,
            query=request.query,
            search_type="keyword",
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keyword search error: {str(e)}")

@app.post("/search/rag", response_model=SearchResponse)
async def rag_search(request: SearchRequest):
    """
    Perform RAG (Retrieval Augmented Generation) search
    Returns products with AI-generated descriptions based on the query context
    """
    global weaviate_service
    
    if not weaviate_service:
        raise HTTPException(status_code=503, detail="Weaviate service not available")
    
    try:
        results = weaviate_service.rag_search(
            query=request.query,
            limit=request.limit
        )
        
        return SearchResponse(
            success=True,
            results=results,
            query=request.query,
            search_type="rag",
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG search error: {str(e)}")

# Utility endpoints
@app.get("/status")
async def get_status():
    """
    Get the current status of the Weaviate service and collection
    """
    global weaviate_service
    
    if not weaviate_service or not weaviate_service.client:
        return {"status": "disconnected", "message": "Weaviate service not connected"}
    
    try:
        # Check if collection exists and get object count
        if weaviate_service.client.collections.exists(weaviate_service.collection_name):
            catalog = weaviate_service.client.collections.get(weaviate_service.collection_name)
            total_objects = catalog.aggregate.over_all(total_count=True)
            
            return {
                "status": "connected",
                "collection_exists": True,
                "total_products": total_objects.total_count,
                "collection_name": weaviate_service.collection_name
            }
        else:
            return {
                "status": "connected",
                "collection_exists": False,
                "message": "Collection not found"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Status check failed: {str(e)}"
        }

if __name__ == "__main__":
    """
    Run the FastAPI application with production-ready settings
    Configure host, port, and reload based on environment
    """
    import sys
    
    # Development vs Production configuration
    if "--dev" in sys.argv:
        # Development mode with auto-reload
        uvicorn.run(
            "weaviate_k8_web:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    else:
        # Production mode
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="warning"
        )