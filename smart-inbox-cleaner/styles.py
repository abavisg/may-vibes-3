"""
Contains all CSS styling for Smart Inbox Cleaner
"""

def get_all_styles():
    """Return all application CSS styles consolidated in one place"""
    return """
<style>
/* ========== GLOBAL STYLING ========== */
html, body, [class*="st-"] {
    font-size: 16px !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
}

/* Main app container */
.main .block-container {
    padding: 1rem 1rem 1rem 1rem !important;
    max-width: 100% !important;
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* ========== BUTTON STYLING ========== */
/* Fixed width for all primary action buttons */
.fixed-width-button button {
    width: 150px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08) !important;
    margin-right: 10px !important;
    margin-bottom: 10px !important;
    border: none !important;
}

.stButton > button[kind="primary"] {
    background-color: #4c7bff !important;
}

/* ========== LAYOUT COMPONENTS ========== */
/* Core layout components */
.app-header {
    display: flex;
    align-items: center;
    background-color: white;
}

.status-bar-left {
    display: inline-block;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    background-color: white; 
    width: 100%;
    box-sizing: border-box;
    overflow: hidden;
}

.status-label {
    display: inline-block;
    background-color: white;
    width: 100%;
    font-size: 20px;
    font-weight: 500;
    margin-bottom: 10px;
}

.status-pills {
    display: flex;
    background-color: white;
    color: black;
    font-size: 13px;
    font-weight: 500;
    gap: 10px;
}

.status-bar-right {
    display: inline-block;
    background-color: white;
    width: 100%;
}

.status-batch {
    margin-left: auto;
    align-self: flex-end;
    background-color: white;
    text-align: right; 
    color: #666; 
    font-size: 0.9rem;
}

.category-pill {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
}

.table-container {
    width: 100%;
    margin-bottom: 0px;
    overflow: auto;
    background-color: white;
    padding: 0px;
}

/* Bottom toolbar */
.bottom-toolbar {
    position: fixed;
    bottom: 50px;
    left: 0;
    right: 0;
    background-color: red;
    z-index: 1000;
    display: flex;
    justify-content: flex-end;
    gap: 50px;
}

/* ========== SIDEBAR STYLING ========== */
[data-testid="stSidebar"] {
    background-color: €ffffee;
    padding: 2rem 1rem;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

[data-testid="stSidebar"] .block-container {
    margin-top: 1rem;
}

/* ========== MODAL STYLING ========== */
/* Modal customization */
div[data-modal-container] > div:first-child {
    border-bottom: none !important;
}

/* Red confirmation button in modal */
div[data-modal-container] div[data-testid="element-container"]:has(button[kind="primary"]) button {
    background-color: #ff4c4c !important;
    border-color: #ff4c4c !important;
}

/* ========== EMAIL TABLE STYLING ========== */
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

def get_debug_styles():
    """Return debugging styles for development mode"""
    return """
<style>
/* Debug layout style rules for containers */
div[data-testid="stVerticalBlock"] {
    background-color: rgba(255, 200, 200, 0.2) !important;
    border: 1px dashed rgba(255, 0, 0, 0.3) !important;
    padding: 2px !important;
    margin-bottom: 5px !important;
}

div[data-testid="stHorizontalBlock"] {
    background-color: rgba(200, 200, 255, 0.2) !important;
    border: 1px dashed rgba(0, 0, 255, 0.3) !important;
    padding: 2px !important;
}

div.element-container, div.stColumn, div.stButton, div.row-widget {
    background-color: rgba(200, 255, 200, 0.2) !important;
    border: 1px dashed rgba(0, 150, 0, 0.3) !important;
    padding: 2px !important;
    margin-bottom: 2px !important;
}

div.stMarkdown {
    background-color: rgba(255, 255, 200, 0.3) !important;
    border: 1px dashed rgba(100, 100, 0, 0.3) !important;
}

/* Sidebar debug styling */
[data-testid="stSidebar"] > div {
    background-color: rgba(255, 200, 0, 0.1) !important;
    border: 1px dashed rgba(255, 150, 0, 0.4) !important;
}
</style>
"""

# Keeping these for backward compatibility, but they now just call get_all_styles
def get_app_styles():
    """Return the minimal application CSS styles - DEPRECATED, use get_all_styles() instead"""
    return get_all_styles() 