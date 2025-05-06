"""
HTML generation functions for Smart Inbox Cleaner UI components
"""
import pandas as pd
import html

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

def generate_email_table_html(df):
    """Generate a custom HTML table to display emails with category pills
    
    Args:
        df: DataFrame containing email data with columns 'date', 'from', 'subject', 'category'
        
    Returns:
        HTML string with a custom styled table
    """
    if df.empty:
        return "<p>No emails to display.</p>"
    
    # Helper function to escape HTML
    def escape_html(text):
        if not isinstance(text, str):
            text = str(text)
        return html.escape(text)
    
    # CSS for email table - included directly in the component
    table_css = """
    <style>
    .email-table-container {
        width: 100%;
        overflow-x: auto;
        margin-top: 20px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }

    .email-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 14px;
    }

    .email-table th {
        background-color: #f8f9fa;
        font-weight: 600;
        padding: 12px 16px;
        text-align: left;
        position: sticky;
        top: 0;
        z-index: 1;
    }

    .email-table td {
        padding: 12px 16px;
        vertical-align: middle;
        border-top: none;
    }

    .email-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }

    .email-table tr:hover {
        background-color: rgba(245, 245, 250, 0.8);
    }

    /* Column widths */
    .date-col {
        width: 140px;
        white-space: nowrap;
    }

    .from-col {
        width: 180px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 240px;
    }

    .subject-col {
        min-width: 300px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .category-col {
        width: 120px;
        text-align: center;
    }

    /* Category select styling */
    .category-select {
        border-radius: 12px;
        padding: 4px 8px;
        font-weight: 500;
        text-align: center;
        width: 120px;
        font-size: 13px;
        cursor: pointer;
        border: none;
        appearance: none;
        -webkit-appearance: none;
        -moz-appearance: none;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="%23666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>');
        background-repeat: no-repeat;
        background-position: right 8px center;
        background-size: 12px;
        padding-right: 24px;
    }

    /* Category specific styles */
    .select-Action {
        background-color: #ff4c4c;
        color: white;
    }

    .select-Read {
        background-color: #4c7bff;
        color: white;
    }

    .select-Information {
        background-color: #4cd97b;
        color: white;
    }

    .select-Events {
        background-color: #ff9e4c;
        color: white;
    }

    .select-Uncategorised {
        background-color: #e0e0e0;
        color: #555;
    }

    /* Style for the dropdown options */
    .category-select option {
        background-color: white;
        color: black;
        font-weight: normal;
    }
    </style>
    """
    
    # JavaScript for handling category changes
    javascript = """
    <script>
    // Function to show debug messages - console only, no visual popup
    function debugLog(message) {
        console.log('[DEBUG]', message);
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        debugLog('DOM Content Loaded - Setting up category selects');
        
        // Get all category selects
        const categorySelects = document.querySelectorAll('.category-select');
        debugLog(`Found ${categorySelects.length} category selects`);
        
        // Create a hidden form for submitting category changes
        const form = document.createElement('form');
        form.style.display = 'none';
        form.id = 'category-update-form';
        form.method = 'post';
        form.target = '_top'; // Target top frame
        
        // Create hidden inputs
        const emailIdInput = document.createElement('input');
        emailIdInput.type = 'hidden';
        emailIdInput.name = 'email_id';
        form.appendChild(emailIdInput);
        
        const categoryInput = document.createElement('input');
        categoryInput.type = 'hidden';
        categoryInput.name = 'category';
        form.appendChild(categoryInput);
        
        // Add form to the document
        document.body.appendChild(form);
        
        // Add change event listener to each select
        categorySelects.forEach((select, index) => {
            // Set initial class based on selected value
            updateSelectStyle(select);
            
            // Add change listener
            select.addEventListener('change', function() {
                // Update the select styling
                updateSelectStyle(this);
                
                // Get email data
                const emailId = this.getAttribute('data-email-id');
                const category = this.value;
                
                debugLog(`Select changed: ${emailId} to ${category}`);
                
                // Display a notification
                showNotification(`Updated to ${category}`);
                
                // Try multiple approaches to update the parent
                
                // 1. Try direct parent URL navigation
                try {
                    const parentUrl = new URL(window.parent.location.href);
                    debugLog(`Parent URL: ${parentUrl.toString()}`);
                    
                    parentUrl.searchParams.set('email_id', emailId);
                    parentUrl.searchParams.set('category', category);
                    
                    debugLog(`Navigating to: ${parentUrl.toString()}`);
                    window.parent.location.href = parentUrl.toString();
                } catch (error) {
                    debugLog(`URL navigation failed: ${error.message}`);
                    
                    // 2. Try using form submission
                    try {
                        debugLog('Trying form submission approach');
                        
                        // Update form action to current parent URL
                        form.action = window.parent.location.href;
                        
                        // Set form values
                        emailIdInput.value = emailId;
                        categoryInput.value = category;
                        
                        // Submit the form
                        form.submit();
                    } catch (formError) {
                        debugLog(`Form submission failed: ${formError.message}`);
                        
                        // 3. Try iframe's own URL as fallback
                        try {
                            debugLog('Falling back to iframe URL update');
                            const currentUrl = new URL(window.location.href);
                            currentUrl.searchParams.set('email_id', emailId);
                            currentUrl.searchParams.set('category', category);
                            window.location.href = currentUrl.toString();
                        } catch (fallbackError) {
                            debugLog(`All approaches failed: ${fallbackError.message}`);
                        }
                    }
                }
            });
        });
        
        // Function to update select styling based on selected value
        function updateSelectStyle(select) {
            // Remove all category classes
            select.classList.remove('select-Action', 'select-Read', 'select-Information', 'select-Events', 'select-Uncategorised');
            // Add the appropriate class for the selected value
            select.classList.add(`select-${select.value}`);
        }
        
        // Function to show a notification
        function showNotification(message) {
            const notification = document.createElement('div');
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: #333;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(notification);
            
            // Fade in
            setTimeout(() => {
                notification.style.opacity = '1';
            }, 10);
            
            // Fade out and remove
            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 2000);
        }
    });
    </script>
    """
    
    # Start building the HTML table
    html_parts = []
    html_parts.append(table_css)  # Include CSS directly in the component
    html_parts.append(javascript)
    html_parts.append('<div class="email-table-container"><table class="email-table">')
    
    # Table header
    html_parts.append('<thead><tr>')
    html_parts.append('<th class="date-col">Date</th>')
    html_parts.append('<th class="from-col">From</th>')
    html_parts.append('<th class="subject-col">Subject</th>')
    html_parts.append('<th class="category-col">Category</th>')
    html_parts.append('</tr></thead>')
    html_parts.append('<tbody>')
    
    # Format date function
    def format_date(date_str):
        try:
            # Parse date and format it as MM-DD-YY HH:MM
            date_obj = pd.to_datetime(date_str)
            return date_obj.strftime("%m-%d-%y %H:%M")
        except:
            return str(date_str)
    
    # All available categories
    categories = ["Action", "Read", "Information", "Events", "Uncategorised"]
    
    # Table rows
    for idx, row in df.iterrows():
        date = escape_html(format_date(row.get('date', '')))
        sender = escape_html(row.get('from', ''))
        subject = escape_html(row.get('subject', ''))
        category = escape_html(row.get('category', 'Uncategorised'))
        
        # Create a unique ID for this email row
        email_id = f"email_{idx}"
        
        # Add the row
        html_parts.append('<tr>')
        html_parts.append(f'<td class="date-col">{date}</td>')
        html_parts.append(f'<td class="from-col" title="{sender}">{sender}</td>')
        html_parts.append(f'<td class="subject-col" title="{subject}">{subject}</td>')
        
        # Create the category dropdown
        html_parts.append('<td class="category-col">')
        html_parts.append(f'<select class="category-select select-{category}" data-email-id="{email_id}">')
        
        # Add options for all categories
        for cat in categories:
            selected = 'selected="selected"' if cat == category else ''
            html_parts.append(f'<option value="{cat}" {selected}>{cat}</option>')
        
        html_parts.append('</select>')
        html_parts.append('</td>')
        html_parts.append('</tr>')
    
    # Close the table
    html_parts.append('</tbody>')
    html_parts.append('</table></div>')
    
    return ''.join(html_parts) 