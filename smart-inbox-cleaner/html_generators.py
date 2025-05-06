"""
HTML generation functions for Smart Inbox Cleaner UI components
"""

def generate_status_html(category_counts, current_batch_size, total_emails):
    """Generate HTML for the inbox status display"""
    status_html = '<div class="inbox-status">'
    status_html += '<div style="font-weight: 500; margin-bottom: 5px;">Inbox Status:</div>'
    status_html += '<div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">'
    
    # Add a pill for each category with the appropriate color
    for cat, count in category_counts.items():
        if cat == "Action":
            color = "#ff4c4c"
            text_color = "white"
        elif cat == "Read":
            color = "#4c7bff"
            text_color = "white"
        elif cat == "Information":
            color = "#4cd97b"
            text_color = "white"
        elif cat == "Events":
            color = "#ff9e4c"
            text_color = "white"
        else:  # Uncategorised or any other
            color = "#e0e0e0"
            text_color = "#555"
            
        status_html += f'<div style="background-color: {color}; color: {text_color}; border-radius: 12px; padding: 3px 12px; font-size: 0.9rem;">{cat}: {count}</div>'
    
    # Add batch info at the end of the category pills
    status_html += f'<div style="margin-left: auto; color: #666; font-size: 0.9rem;">Batch: {current_batch_size} of {total_emails}</div>'
    
    status_html += '</div></div>'
    return status_html

def generate_progress_html(progress_text):
    """Generate HTML for progress indicator"""
    return f"""
    <div style="padding-top: 8px; color: #555; display: flex; align-items: center;">
        <div style="width: 12px; height: 12px; background-color: #4c7bff; border-radius: 50%; margin-right: 8px;"></div>
        {progress_text}
    </div>
    """

def generate_complete_html(progress_text):
    """Generate HTML for completion indicator"""
    return f"""
    <div style="padding-top: 8px; color: #4cd97b; display: flex; align-items: center;">
        <div style="width: 12px; height: 12px; background-color: #4cd97b; border-radius: 50%; margin-right: 8px;"></div>
        {progress_text}
    </div>
    """

def generate_category_pill_js():
    """Generate JavaScript code to transform category text into colored text"""
    return """
    <script>
    // Category color mapping
    const categoryColors = {
        'Action': '#ff4c4c',     // Red
        'Read': '#4c7bff',       // Blue
        'Information': '#4cd97b', // Green
        'Events': '#ff9e4c',     // Orange
        'Uncategorised': '#666666' // Dark gray
    };
    
    // Function to apply category text colors - more aggressively targeting all elements
    function applyCategoryTextColors() {
        // Apply to all directly visible category selects first
        document.querySelectorAll('.stDataFrame select').forEach(select => {
            if (!select) return;
            
            const category = select.value;
            if (!category || !categoryColors[category]) return;
            
            // Color the select text directly
            select.style.setProperty('color', categoryColors[category], 'important');
            select.style.setProperty('font-weight', '600', 'important');
            select.style.setProperty('font-size', '15px', 'important');
            select.style.setProperty('text-align', 'center', 'important');
            
            // Clean up the select appearance
            select.style.setProperty('border', 'none', 'important');
            select.style.setProperty('background-color', 'transparent', 'important');
            select.style.setProperty('appearance', 'none', 'important');
            select.style.setProperty('-webkit-appearance', 'none', 'important');
            select.style.setProperty('-moz-appearance', 'none', 'important');
            
            // Set attribute on containing row
            const row = select.closest('tr');
            if (row) {
                row.setAttribute('data-category', category);
            }
            
            // Color all text elements in the same cell
            const cell = select.closest('td');
            if (cell) {
                cell.querySelectorAll('div, span, p').forEach(element => {
                    element.style.setProperty('color', categoryColors[category], 'important');
                    element.style.setProperty('font-weight', '600', 'important');
                });
            }
            
            // Add change event listener if not already added
            if (!select.hasAttribute('data-color-listener')) {
                select.addEventListener('change', function() {
                    const newCategory = this.value;
                    if (categoryColors[newCategory]) {
                        this.style.setProperty('color', categoryColors[newCategory], 'important');
                        
                        // Update row attribute
                        const row = this.closest('tr');
                        if (row) {
                            row.setAttribute('data-category', newCategory);
                        }
                        
                        // Update cell elements
                        const cell = this.closest('td');
                        if (cell) {
                            cell.querySelectorAll('div, span, p').forEach(element => {
                                element.style.setProperty('color', categoryColors[newCategory], 'important');
                            });
                        }
                    }
                });
                select.setAttribute('data-color-listener', 'true');
            }
        });
        
        // Also look for category cells via their column name
        document.querySelectorAll('.stDataFrame th').forEach(header => {
            if (header.textContent.trim() === 'Category') {
                const columnIndex = Array.from(header.parentNode.children).indexOf(header);
                
                // Get all cells in this column
                document.querySelectorAll('.stDataFrame tbody tr').forEach(row => {
                    const cell = row.children[columnIndex];
                    if (!cell) return;
                    
                    // Find the category value within this cell
                    const select = cell.querySelector('select');
                    if (!select) return;
                    
                    const category = select.value;
                    if (!categoryColors[category]) return;
                    
                    // Apply the color to the cell and all its children
                    cell.style.setProperty('color', categoryColors[category], 'important');
                    cell.querySelectorAll('*').forEach(el => {
                        el.style.setProperty('color', categoryColors[category], 'important');
                    });
                });
            }
        });
    }
    
    // Run on load and periodically
    document.addEventListener('DOMContentLoaded', function() {
        // Run immediately 
        applyCategoryTextColors();
        
        // Run after a delay to catch lazy-loaded elements
        setTimeout(applyCategoryTextColors, 500);
        setTimeout(applyCategoryTextColors, 1000);
        setTimeout(applyCategoryTextColors, 2000);
        
        // Set up mutation observer to catch dynamic changes
        const observer = new MutationObserver(function() {
            applyCategoryTextColors();
        });
        
        // Watch the entire document for changes
        observer.observe(document.body, { 
            childList: true, 
            subtree: true,
            attributes: true,
            attributeFilter: ['value', 'class']
        });
        
        // Also run periodically to be safe
        setInterval(applyCategoryTextColors, 1000);
    });
    </script>
    """ 