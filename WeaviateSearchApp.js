import React, { useState, useRef } from 'react';
import { Upload, Search, Database, Zap, Brain, MessageSquare, AlertCircle, CheckCircle, Loader2, X } from 'lucide-react';

const WeaviateSearchApp = () => {
  // State management
  const [activeTab, setActiveTab] = useState('upload');
  const [products, setProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({ type: '', message: '' });
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const fileInputRef = useRef(null);

  // Sample products for reference
  const sampleProducts = [
    {
      "product_id": "prod-001",
      "name": "Wireless Bluetooth Headphones",
      "description": "Premium noise-cancelling wireless headphones with 30-hour battery life. Perfect for music lovers and professionals.",
      "category": "Electronics",
      "price": 199.99,
      "brand": "AudioTech",
      "tags": ["wireless", "bluetooth", "noise-cancelling", "premium"],
      "specifications": {
        "battery_life": "30 hours",
        "connectivity": "Bluetooth 5.0",
        "weight": "250g"
      }
    }
  ];

  // Poka-yoke: Validate JSON structure
  const validateProductStructure = (product) => {
    const requiredFields = ['product_id', 'name', 'description', 'category', 'price', 'brand', 'tags'];
    return requiredFields.every(field => product.hasOwnProperty(field));
  };

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Poka-yoke: Validate file type
    if (!file.name.endsWith('.json')) {
      setUploadStatus({ type: 'error', message: 'Please upload a JSON file' });
      return;
    }

    setIsLoading(true);
    setUploadStatus({ type: '', message: '' });

    try {
      const text = await file.text();
      const jsonData = JSON.parse(text);
      
      // Poka-yoke: Ensure it's an array
      const productsArray = Array.isArray(jsonData) ? jsonData : [jsonData];
      
      // Poka-yoke: Validate each product structure
      const invalidProducts = productsArray.filter(product => !validateProductStructure(product));
      if (invalidProducts.length > 0) {
        throw new Error(`Invalid product structure found. Missing required fields in ${invalidProducts.length} products.`);
      }

      setProducts(productsArray);
      setUploadStatus({ 
        type: 'success', 
        message: `Successfully loaded ${productsArray.length} products` 
      });

      // Auto-switch to search tab after successful upload
      setTimeout(() => setActiveTab('hybrid'), 1500);

    } catch (error) {
      setUploadStatus({ 
        type: 'error', 
        message: `Error parsing JSON: ${error.message}` 
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Simulate API calls to Weaviate (replace with actual API calls)
  const performSearch = async (searchType) => {
    if (!searchQuery.trim()) return;
    
    setIsLoading(true);
    setSearchResults([]);

    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock search results based on query and type
      const mockResults = products.filter(product => 
        product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        product.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        product.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      ).slice(0, 5);

      // Add mock metadata based on search type
      const resultsWithMetadata = mockResults.map((product, index) => ({
        ...product,
        _metadata: {
          score: searchType === 'keyword' ? 0.95 - (index * 0.1) : undefined,
          distance: searchType === 'vector' ? 0.1 + (index * 0.05) : undefined,
          generated: searchType === 'rag' ? `This ${product.name} would be perfect for ${searchQuery} because of its ${product.tags.join(', ')} features and ${product.category.toLowerCase()} design.` : undefined
        }
      }));

      setSearchResults(resultsWithMetadata);
      setConnectionStatus('connected');

    } catch (error) {
      setUploadStatus({ 
        type: 'error', 
        message: `Search error: ${error.message}` 
      });
      setConnectionStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  // Download sample JSON
  const downloadSampleJson = () => {
    const dataStr = JSON.stringify(sampleProducts, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'sample_products.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  const tabs = [
    { id: 'upload', label: 'Upload Products', icon: Upload },
    { id: 'hybrid', label: 'Hybrid Search', icon: Zap },
    { id: 'keyword', label: 'Keyword Search', icon: Search },
    { id: 'vector', label: 'Vector Search', icon: Brain },
    { id: 'rag', label: 'RAG Search', icon: MessageSquare }
  ];

  const TabButton = ({ tab, isActive, onClick }) => {
    const Icon = tab.icon;
    return (
      <button
        onClick={() => onClick(tab.id)}
        className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
          isActive 
            ? 'bg-blue-600 text-white shadow-md' 
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        <Icon size={18} />
        <span>{tab.label}</span>
      </button>
    );
  };

  const StatusMessage = ({ status }) => {
    if (!status.message) return null;
    
    const isError = status.type === 'error';
    const isSuccess = status.type === 'success';
    
    return (
      <div className={`flex items-center space-x-2 p-3 rounded-lg ${
        isError ? 'bg-red-50 text-red-700' : isSuccess ? 'bg-green-50 text-green-700' : 'bg-blue-50 text-blue-700'
      }`}>
        {isError && <AlertCircle size={18} />}
        {isSuccess && <CheckCircle size={18} />}
        <span>{status.message}</span>
      </div>
    );
  };

  const ConnectionIndicator = () => (
    <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
      connectionStatus === 'connected' ? 'bg-green-100 text-green-700' :
      connectionStatus === 'error' ? 'bg-red-100 text-red-700' :
      'bg-gray-100 text-gray-600'
    }`}>
      <div className={`w-2 h-2 rounded-full ${
        connectionStatus === 'connected' ? 'bg-green-500' :
        connectionStatus === 'error' ? 'bg-red-500' :
        'bg-gray-400'
      }`} />
      <span>
        {connectionStatus === 'connected' ? 'Connected' :
         connectionStatus === 'error' ? 'Connection Error' :
         'Disconnected'}
      </span>
    </div>
  );

  const SearchResults = ({ results, searchType }) => {
    if (results.length === 0 && !isLoading) {
      return (
        <div className="text-center py-8 text-gray-500">
          <Search size={48} className="mx-auto mb-4 text-gray-300" />
          <p>No results found. Try a different search term.</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {results.map((product, index) => (
          <div key={product.product_id} className="bg-white rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-lg text-gray-800">{product.name}</h3>
              <span className="text-2xl font-bold text-green-600">${product.price}</span>
            </div>
            
            <div className="flex items-center space-x-4 mb-3 text-sm text-gray-600">
              <span className="bg-gray-100 px-2 py-1 rounded">{product.category}</span>
              <span className="text-gray-500">{product.brand}</span>
            </div>
            
            <p className="text-gray-700 mb-3">{product.description}</p>
            
            <div className="flex flex-wrap gap-1 mb-3">
              {product.tags.map(tag => (
                <span key={tag} className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs">
                  {tag}
                </span>
              ))}
            </div>

            {/* Metadata based on search type */}
            {product._metadata && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                {product._metadata.score && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Relevance Score:</span> {product._metadata.score.toFixed(4)}
                  </div>
                )}
                {product._metadata.distance && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Vector Distance:</span> {product._metadata.distance.toFixed(4)}
                  </div>
                )}
                {product._metadata.generated && (
                  <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm font-medium text-blue-800">AI Generated:</span>
                    <p className="text-sm text-blue-700 mt-1">{product._metadata.generated}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            <Database className="inline-block mr-3" size={40} />
            Weaviate Product Search
          </h1>
          <p className="text-gray-600">Upload products and test different search capabilities</p>
          <div className="mt-4">
            <ConnectionIndicator />
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {tabs.map(tab => (
            <TabButton
              key={tab.id}
              tab={tab}
              isActive={activeTab === tab.id}
              onClick={setActiveTab}
            />
          ))}
        </div>

        {/* Status Messages */}
        <div className="mb-6">
          <StatusMessage status={uploadStatus} />
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          {activeTab === 'upload' && (
            <div className="max-w-2xl mx-auto">
              <h2 className="text-2xl font-semibold mb-6 text-center">Upload Product Data</h2>
              
              {/* Sample Download */}
              <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium mb-2">Need a sample file?</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Download our sample JSON format to see the expected structure.
                </p>
                <button
                  onClick={downloadSampleJson}
                  className="text-blue-600 hover:text-blue-800 underline text-sm"
                >
                  Download sample_products.json
                </button>
              </div>

              {/* File Upload */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                <Upload size={48} className="mx-auto text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">Upload Product JSON File</p>
                <p className="text-gray-500 mb-4">Drag and drop or click to select</p>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors flex items-center space-x-2 mx-auto"
                >
                  {isLoading && <Loader2 size={18} className="animate-spin" />}
                  <span>{isLoading ? 'Processing...' : 'Select JSON File'}</span>
                </button>
              </div>

              {products.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-medium mb-3">Loaded Products ({products.length})</h3>
                  <div className="max-h-60 overflow-y-auto bg-gray-50 rounded-lg p-4">
                    {products.map(product => (
                      <div key={product.product_id} className="flex justify-between items-center py-2 border-b last:border-b-0">
                        <span className="font-medium">{product.name}</span>
                        <span className="text-gray-500">{product.category}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {(['hybrid', 'keyword', 'vector', 'rag'].includes(activeTab)) && (
            <div>
              <div className="max-w-2xl mx-auto mb-8">
                <h2 className="text-2xl font-semibold mb-6 text-center">
                  {tabs.find(t => t.id === activeTab)?.label}
                </h2>
                
                {/* Search Input */}
                <div className="flex space-x-4">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Enter search query (e.g., 'comfortable headphones for work')"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      onKeyPress={(e) => e.key === 'Enter' && performSearch(activeTab)}
                    />
                  </div>
                  <button
                    onClick={() => performSearch(activeTab)}
                    disabled={isLoading || !searchQuery.trim() || products.length === 0}
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors flex items-center space-x-2"
                  >
                    {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
                    <span>{isLoading ? 'Searching...' : 'Search'}</span>
                  </button>
                </div>

                {products.length === 0 && (
                  <p className="text-center text-gray-500 mt-4">
                    Please upload products first to enable search functionality.
                  </p>
                )}
              </div>

              {/* Search Results */}
              {isLoading ? (
                <div className="text-center py-12">
                  <Loader2 size={48} className="mx-auto animate-spin text-blue-600 mb-4" />
                  <p className="text-gray-600">Searching products...</p>
                </div>
              ) : (
                <SearchResults results={searchResults} searchType={activeTab} />
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Weaviate v4 Frontend • Built with React and Tailwind CSS</p>
        </div>
      </div>
    </div>
  );
};

export default WeaviateSearchApp;