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
    background-color: #efffee;
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

/* Email table styles were removed from here as they are embedded in html_generators.py */


</style>
"""

# Keeping these for backward compatibility, but they now just call get_all_styles
def get_app_styles():
    """Return the minimal application CSS styles - DEPRECATED, use get_all_styles() instead"""
    return get_all_styles() 