/**
 * AI Node Builder Documentation App
 * A standalone SPA for browsing node documentation
 */
class DocsApp {
    constructor() {
        this.registry = null;
        this.currentRoute = null;
        this.searchTimeout = null;
        this.init();
    }
    
    async init() {
        try {
            await this.loadRegistry();
            this.setupRouting();
            this.setupSearch();
            this.renderNavigation();
            this.route(); // Initial route
        } catch (error) {
            console.error('Failed to initialize docs app:', error);
            this.showError('Failed to load documentation system');
        }
    }
    
    async loadRegistry() {
        try {
            const response = await fetch('/api/docs/registry');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            this.registry = await response.json();
            console.log('Loaded documentation registry:', this.registry);
        } catch (error) {
            console.error('Failed to load documentation registry:', error);
            this.registry = { categories: {}, nodes: {} };
            throw error;
        }
    }
    
    setupRouting() {
        window.addEventListener('hashchange', () => this.route());
        
        // Handle browser back/forward buttons
        window.addEventListener('popstate', () => this.route());
    }
    
    route() {
        const hash = window.location.hash.slice(1); // Remove #
        const [type, identifier] = hash.split('/');
        
        // Clear active navigation items
        document.querySelectorAll('.nav-category a').forEach(a => a.classList.remove('active'));
        
        switch(type) {
            case 'node':
                this.showNodeDocumentation(identifier);
                this.setActiveNavItem(identifier);
                break;
            case 'category':
                if (identifier === 'guides') {
                    this.showGuidesCategory();
                } else {
                    this.showCategoryBrowser(identifier);
                }
                break;
            case 'guide':
                this.showGuide(identifier);
                break;
            case 'search':
                this.showSearchResults(decodeURIComponent(identifier));
                break;
            default:
                this.showHomePage();
        }
    }
    
    setActiveNavItem(nodeName) {
        const link = document.querySelector(`a[href="#node/${nodeName}"]`);
        if (link) {
            link.classList.add('active');
        }
    }
    
    async showNodeDocumentation(nodeName) {
        if (!nodeName) {
            this.showError('No node specified');
            return;
        }
        
        try {
            this.showLoading('Loading documentation...');
            const response = await fetch(`/api/docs/content/${nodeName}`);
            if (!response.ok) {
                throw new Error(`Documentation not found for node: ${nodeName}`);
            }
            const doc = await response.json();
            this.renderMarkdown(doc.content, doc.metadata);
        } catch (error) {
            console.error('Error loading node documentation:', error);
            this.showError(`Documentation not found for node: ${nodeName}`);
        }
    }
    
    showCategoryBrowser(categoryName) {
        if (!this.registry.categories[categoryName]) {
            this.showError(`Category not found: ${categoryName}`);
            return;
        }
        
        const category = this.registry.categories[categoryName];
        let html = `
            <div class="breadcrumb">
                <a href="#" class="back-button">← Back to Home</a>
            </div>
            <h1>${categoryName} Nodes</h1>
            <p>${category.length} node${category.length !== 1 ? 's' : ''} available in this category.</p>
            <div class="category-nodes">
        `;
        
        category.forEach(node => {
            html += `
                <div class="category-card">
                    <h3><a href="#node/${node.name}">${node.title}</a></h3>
                    <p>${node.description || 'No description available.'}</p>
                    <div class="node-meta">
                        ${node.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        this.setContent(html);
        document.title = `${categoryName} Nodes - AI Node Builder Docs`;
    }
    
    showGuide(guideName) {
        this.showLoading('Loading guide...');
        
        fetch(`/api/docs/guide/${guideName}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Guide not found: ${guideName}`);
                }
                return response.json();
            })
            .then(guide => {
                this.renderMarkdown(guide.content, guide.metadata);
            })
            .catch(error => {
                console.error('Error loading guide:', error);
                this.showError(`Guide not found: ${guideName}`);
            });
    }
    
    showGuidesCategory() {
        const html = `
            <div class="breadcrumb">
                <a href="#" class="back-button">← Back to Home</a>
            </div>
            <h1>Guides</h1>
            <p>Development guides and documentation for AI Node Builder.</p>
            <div class="category-nodes">
                <div class="category-card">
                    <h3><a href="#guide/node-creation">Node Creation Guide</a></h3>
                    <p>Comprehensive walkthrough for creating custom nodes for AI Node Builder</p>
                </div>
                <div class="category-card">
                    <h3><a href="#guide/node-documentation">Node Documentation Guide</a></h3>
                    <p>Guide for creating documentation for AI Node Builder nodes</p>
                </div>
                <div class="category-card">
                    <h3><a href="#guide/devdocs">Developer Documentation</a></h3>
                    <p>Project architecture and development guide for AI Node Builder</p>
                </div>
            </div>
        `;
        this.setContent(html);
        document.title = 'Guides - AI Node Builder Docs';
    }
    
    renderMarkdown(content, metadata) {
        try {
            const html = marked.parse(content);
            const categoryName = metadata.category || 'Unknown';
            
            // Add breadcrumb navigation
            const breadcrumbHtml = `
                <div class="breadcrumb">
                    <a href="#" class="back-button">← Back to Home</a>
                    <span> / </span>
                    <a href="#category/${categoryName}" class="category-link">${categoryName}</a>
                </div>
            `;
            
            this.setContent(breadcrumbHtml + html);
            
            // Update page title
            const title = metadata.title || metadata.name || 'Documentation';
            document.title = `${title} - AI Node Builder Docs`;
        } catch (error) {
            console.error('Error rendering markdown:', error);
            this.showError('Error rendering documentation content');
        }
    }
    
    renderNavigation() {
        const navContent = document.getElementById('nav-content');
        
        if (!this.registry || Object.keys(this.registry.categories).length === 0) {
            navContent.innerHTML = '<div class="nav-section"><p>No documentation available</p></div>';
            return;
        }
        
        let html = `
            <div class="nav-section">
                <h3>Guides</h3>
                <div class="nav-category">
                    <ul>
                        <li><a href="#guide/node-creation">Node Creation Guide</a></li>
                        <li><a href="#guide/node-documentation">Node Documentation Guide</a></li>
                        <li><a href="#guide/devdocs">Developer Documentation</a></li>
                    </ul>
                </div>
            </div>
            <div class="nav-section">
                <h3>Node Categories</h3>
        `;
        
        // Sort categories alphabetically
        const sortedCategories = Object.entries(this.registry.categories)
            .sort(([a], [b]) => a.localeCompare(b));
        
        sortedCategories.forEach(([category, nodes]) => {
            if (nodes.length === 0) return;
            
            html += `
                <div class="nav-category">
                    <h4>${category} (${nodes.length})</h4>
                    <ul>
            `;
            
            // Sort nodes by title
            const sortedNodes = nodes.sort((a, b) => a.title.localeCompare(b.title));
            
            sortedNodes.forEach(node => {
                html += `<li><a href="#node/${node.name}">${node.title}</a></li>`;
            });
            
            html += '</ul></div>';
        });
        
        html += '</div>';
        
        navContent.innerHTML = html;
    }
    
    setupSearch() {
        const searchInput = document.getElementById('search');
        const searchResults = document.getElementById('search-results');
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            // Clear previous timeout
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            if (query.length < 2) {
                searchResults.style.display = 'none';
                return;
            }
            
            // Debounce search
            this.searchTimeout = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });
        
        // Hide search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
        
        // Handle keyboard navigation
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchResults.style.display = 'none';
                searchInput.blur();
            }
        });
    }
    
    performSearch(query) {
        const results = this.search(query);
        const searchResults = document.getElementById('search-results');
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item">No results found</div>';
        } else {
            let html = '';
            results.slice(0, 10).forEach(result => { // Limit to 10 results
                html += `
                    <div class="search-result-item" onclick="docsApp.navigateToNode('${result.name}')">
                        <div class="search-result-title">${result.title}</div>
                        <div class="search-result-description">${result.description || 'No description'}</div>
                    </div>
                `;
            });
            searchResults.innerHTML = html;
        }
        
        searchResults.style.display = 'block';
    }
    
    navigateToNode(nodeName) {
        window.location.hash = `node/${nodeName}`;
        document.getElementById('search-results').style.display = 'none';
        document.getElementById('search').value = '';
    }
    
    search(query) {
        if (!this.registry) return [];
        
        const lowerQuery = query.toLowerCase();
        return Object.values(this.registry.nodes).filter(node => 
            node.title.toLowerCase().includes(lowerQuery) ||
            node.description.toLowerCase().includes(lowerQuery) ||
            node.name.toLowerCase().includes(lowerQuery) ||
            node.category.toLowerCase().includes(lowerQuery) ||
            node.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
        );
    }
    
    showSearchResults(query) {
        const results = this.search(query);
        let html = `<h1>Search Results for "${query}"</h1>`;
        
        if (results.length === 0) {
            html += '<p>No results found. Try different keywords or check the navigation for available nodes.</p>';
        } else {
            html += `<p>Found ${results.length} result${results.length !== 1 ? 's' : ''}:</p><div class="search-results-list">`;
            results.forEach(result => {
                html += `
                    <div class="category-card">
                        <h3><a href="#node/${result.name}">${result.title}</a></h3>
                        <p><strong>Category:</strong> ${result.category}</p>
                        <p>${result.description || 'No description available.'}</p>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        this.setContent(html);
        document.title = `Search: ${query} - AI Node Builder Docs`;
    }
    
    showHomePage() {
        if (!this.registry) {
            this.showError('Documentation registry not loaded');
            return;
        }
        
        const totalNodes = Object.keys(this.registry.nodes).length;
        const totalCategories = Object.keys(this.registry.categories).length;
        
        let html = `
            <h1>AI Node Builder Documentation</h1>
            <p>Welcome to the AI Node Builder documentation system. This is your comprehensive guide to all available nodes and their usage.</p>
            
            <div style="margin: 30px 0;">
                <p><strong>${totalNodes}</strong> nodes available across <strong>${totalCategories}</strong> categories</p>
                <p><em>Last updated: ${new Date(this.registry.last_updated).toLocaleString()}</em></p>
            </div>
            
            <h2>Browse by Category</h2>
            
            <div class="category-card" data-category="guides">
                <h3><a href="#category/guides">guides</a></h3>
                <p>3 guides available</p>
                <p>Browse development guides and documentation →</p>
            </div>
        `;
        
        Object.entries(this.registry.categories).forEach(([category, nodes]) => {
            if (nodes.length === 0) return;
            
            html += `
                <div class="category-card" data-category="${category}">
                    <h3><a href="#category/${category}">${category}</a></h3>
                    <p>${nodes.length} node${nodes.length !== 1 ? 's' : ''} available</p>
                    <p>Browse all ${category.toLowerCase()} nodes →</p>
                </div>
            `;
        });
        
        html += `
            <h2>Quick Start</h2>
            <ul>
                <li>Use the search box above to find specific nodes</li>
                <li>Browse categories in the sidebar</li>
                <li>Right-click on nodes in the main editor to access their documentation</li>
                <li>Click the 📚 Docs button in the main interface to return here</li>
            </ul>
        `;
        
        this.setContent(html);
        
        // Add click event listeners to category cards
        document.querySelectorAll('.category-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't trigger if clicking on the actual link
                if (e.target.tagName === 'A') return;
                
                const category = card.dataset.category;
                window.location.hash = `#category/${category}`;
                this.route(); // Manually trigger routing
            });
            
            // Make the card appear clickable
            card.style.cursor = 'pointer';
        });
        
        document.title = 'AI Node Builder Documentation';
    }
    
    showLoading(message = 'Loading...') {
        this.setContent(`<div class="loading">${message}</div>`);
    }
    
    showError(message) {
        this.setContent(`<div class="error">❌ ${message}</div>`);
        console.error('Docs error:', message);
    }
    
    setContent(html) {
        document.getElementById('doc-content').innerHTML = html;
        
        // Add click handlers to make images open in new tab
        this.setupImageClickHandlers();
    }
    
    setupImageClickHandlers() {
        const images = document.querySelectorAll('#doc-content img, .content img');
        images.forEach(img => {
            img.addEventListener('click', () => {
                window.open(img.src, '_blank');
            });
            
            // Add title attribute for better UX
            img.title = 'Click to open image in new tab';
        });
    }
}

// Global instance for event handlers
let docsApp;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    docsApp = new DocsApp();
});