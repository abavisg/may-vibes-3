"""
Contains all CSS styling for Smart Inbox Cleaner
"""

def get_app_styles():
    """Return the main application CSS styles"""
    return """
<style>
/* Global styling */
html, body, [class*="st-"] {
    font-size: 16px !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
}

/* Main app container */
.main .block-container {
    padding: 1rem 1rem 1rem 1rem !important;
    max-width: 100% !important;
}

/* Card styling for the entire app */
.main .block-container {
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* Enhanced Table Layout - Better Consistency */
.stDataFrame {
    width: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif !important;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* Table headers - more consistent appearance */
.stDataFrame thead th {
    background-color: #f8f9fa !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    text-transform: none !important;
    border-bottom: 1px solid #eaeaea !important;
    white-space: nowrap !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 1 !important;
    letter-spacing: 0.01em !important;
}

/* Cell styling for consistent layout */
.stDataFrame [data-testid="StyledDataFrameDataCell"] {
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
    vertical-align: middle !important;
    line-height: 1.4 !important;
    letter-spacing: 0.01em !important;
}

/* Row styling for consistency */
.stDataFrame tbody tr {
    border-bottom: 1px solid #f0f0f0 !important;
    height: 3.5rem !important;
    transition: background-color 0.15s ease !important;
}

/* Row hover effect */
.stDataFrame tbody tr:hover {
    background-color: rgba(245, 245, 250, 0.8) !important;
    transition: background-color 0.15s ease !important;
}

/* Last row in table - no border */
.stDataFrame tbody tr:last-child {
    border-bottom: none !important;
}

/* Better width control for columns */
.stDataFrame .column-category {
    width: 120px !important;
    min-width: 120px !important;
    max-width: 120px !important;
}

.stDataFrame .column-date {
    width: 140px !important;
    min-width: 140px !important;
    max-width: 140px !important;
}

.stDataFrame .column-from {
    width: 180px !important;
    min-width: 180px !important;
    max-width: 240px !important;
}

.stDataFrame .column-subject {
    min-width: 300px !important;
}

.stDataFrame .column-select {
    width: 60px !important;
    min-width: 60px !important;
    max-width: 60px !important;
}

/* Checkbox styling in table */
.stDataFrame input[type="checkbox"] {
    width: 16px !important;
    height: 16px !important;
    margin: 0 auto !important;
    display: block !important;
}

/* Hide row header numbers */
.stDataFrame [data-testid="StyledDataFrameRowHeader"] {
    display: none;
}

/* Category pills styling */
.stDataFrame [data-testid="StyledDataFrameDataCell"] div:contains("Action") {
    background-color: #ff4c4c !important;
    color: white !important;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 500;
    display: inline-block;
    text-align: center;
    min-width: 80px;
}

/* Modal customization */
div[data-modal-container] > div:first-child {
    border-bottom: none !important;
}

/* Red confirmation button in modal */
div[data-modal-container] div[data-testid="element-container"]:has(button[kind="primary"]) button {
    background-color: #ff4c4c !important;
    border-color: #ff4c4c !important;
}

.stDataFrame [data-testid="StyledDataFrameDataCell"] div:contains("Read") {
    background-color: #4c7bff !important;
    color: white !important;
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 500;
    display: inline-block;
    text-align: center;
    min-width: 80px;
}

/* Add additional more specific selectors to target the categories */
.stDataFrame th:contains("Category") ~ td div {
    padding: 2px 10px !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    display: inline-block !important;
    text-align: center !important;
}

.stDataFrame select[aria-label="Category"] option[value="Action"] {
    background-color: #ff4c4c !important;
    color: white !important;
}

.stDataFrame select[aria-label="Category"] option[value="Read"] {
    background-color: #4c7bff !important;
    color: white !important;
}

.stDataFrame select[aria-label="Category"] option[value="Information"] {
    background-color: #4cd97b !important;
    color: white !important;
}

.stDataFrame select[aria-label="Category"] option[value="Events"] {
    background-color: #ff9e4c !important;
    color: white !important;
}

.stDataFrame select[aria-label="Category"] option[value="Uncategorised"] {
    background-color: #e0e0e0 !important;
    color: #555 !important;
}

/* Additional selector to ensure category pills are properly formatted */
.stDataFrame [data-testid="stDataFrameCell"] select option {
    padding: 4px !important;
}

/* Button styling */
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

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: white;
    padding: 2rem 1rem;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

[data-testid="stSidebar"] .block-container {
    margin-top: 1rem;
}

/* Processing overlay styling */
.processing-overlay {
    position: relative;
    z-index: 1000;
    background-color: rgba(245, 245, 250, 0.95);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(0, 0, 0, 0.05);
}

/* Disabled table styling during processing */
.disabled-table [data-testid="stDataFrame"] {
    opacity: 0.8;
    position: relative;
    transition: all 0.3s ease;
}

.disabled-table [data-testid="stDataFrame"]::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(245, 245, 250, 0.4);
    border-radius: 8px;
    pointer-events: none;
    z-index: 1;
}

/* Inbox status styling */
.inbox-status {
    text-align: left;
    margin-bottom: 1rem;
}

/* Remove padding from header */
header {
    display: none;
}

/* Custom category formatter */
.category-pill {
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 500;
    display: inline-block;
    text-align: center;
    min-width: 80px;
}
.category-Action {
    background-color: #ff4c4c !important;
    color: white !important;
}
.category-Read {
    background-color: #4c7bff !important;
    color: white !important;
}
.category-Information {
    background-color: #4cd97b !important;
    color: white !important;
}
.category-Events {
    background-color: #ff9e4c !important;
    color: white !important;
}
.category-Uncategorised {
    background-color: #e0e0e0 !important;
    color: #555 !important;
}

/* Set color and appearance for select dropdown */
.stDataFrame [data-testid="stDataFrameCell"] select {
    border-radius: 12px !important;
    padding: 2px 8px !important;
}

/* Category pills styling */
[data-testid="stDataFrameCell"] [data-testid="column-Category"] select {
    background-color: var(--category-color, #e0e0e0);
    color: var(--category-text-color, #333);
    border-radius: 12px;
    padding: 2px 10px;
    font-weight: 500;
    text-align: center;
    border: none;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    min-width: 120px;
}

/* Set colors for different category values */
[data-testid="stDataFrameCell"] [data-testid="column-Category"] select option[value="Action"] {
    background-color: #ff4c4c;
    color: white;
}

[data-testid="stDataFrameCell"] [data-testid="column-Category"] select option[value="Read"] {
    background-color: #4c7bff;
    color: white;
}

[data-testid="stDataFrameCell"] [data-testid="column-Category"] select option[value="Information"] {
    background-color: #4cd97b;
    color: white;
}

[data-testid="stDataFrameCell"] [data-testid="column-Category"] select option[value="Events"] {
    background-color: #ff9e4c;
    color: white;
}

[data-testid="stDataFrameCell"] [data-testid="column-Category"] select option[value="Uncategorised"] {
    background-color: #e0e0e0;
    color: #555;
}

/* Category cells styling */
.category-Action {
    --category-color: #ff4c4c !important;
    --category-text-color: white !important;
}

.category-Read {
    --category-color: #4c7bff !important;
    --category-text-color: white !important;
}

.category-Information {
    --category-color: #4cd97b !important;
    --category-text-color: white !important;
}

.category-Events {
    --category-color: #ff9e4c !important;
    --category-text-color: white !important;
}

.category-Uncategorised {
    --category-color: #e0e0e0 !important;
    --category-text-color: #555 !important;
}

/* Row styling for category colors */
.stDataFrame tbody tr:has(td:has(div:has(select option[value="Action"]:checked))) {
    background-color: rgba(255, 76, 76, 0.12) !important;
}

.stDataFrame tbody tr:has(td:has(div:has(select option[value="Read"]:checked))) {
    background-color: rgba(76, 123, 255, 0.12) !important;
}

.stDataFrame tbody tr:has(td:has(div:has(select option[value="Information"]:checked))) {
    background-color: rgba(76, 217, 123, 0.12) !important;
}

.stDataFrame tbody tr:has(td:has(div:has(select option[value="Events"]:checked))) {
    background-color: rgba(255, 158, 76, 0.12) !important;
}

/* Truncate long text with ellipsis */
.stDataFrame .column-subject div,
.stDataFrame .column-from div {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
}

/* Ensure proper alignment of all elements in cells */
.stDataFrame td, .stDataFrame th {
    text-align: left !important;
}

/* Data editor container styling */
[data-testid="stDataFrame"] > div:first-child {
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* Custom scrollbar styling for the table */
.stDataFrame::-webkit-scrollbar {
    width: 10px !important;
    height: 10px !important;
}

.stDataFrame::-webkit-scrollbar-track {
    background: #f1f1f1 !important;
    border-radius: 5px !important;
}

.stDataFrame::-webkit-scrollbar-thumb {
    background: #c1c1c1 !important;
    border-radius: 5px !important;
}

.stDataFrame::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8 !important;
}

/* Apply scrollbar styling to the data editor content */
[data-testid="stDataFrame"] [data-testid="StyledDataFrame"]::-webkit-scrollbar {
    width: 8px !important;
    height: 8px !important;
}

[data-testid="stDataFrame"] [data-testid="StyledDataFrame"]::-webkit-scrollbar-track {
    background: #f1f1f1 !important;
    border-radius: 4px !important;
}

[data-testid="stDataFrame"] [data-testid="StyledDataFrame"]::-webkit-scrollbar-thumb {
    background: #c1c1c1 !important;
    border-radius: 4px !important;
}

[data-testid="stDataFrame"] [data-testid="StyledDataFrame"]::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8 !important;
}

/* Enhanced category text styling - use stronger selectors */
.stDataFrame tr[data-category="Action"] select,
.stDataFrame tr[data-category="Action"] div,
.stDataFrame select[value="Action"] {
    color: #ff4c4c !important;
    font-weight: 600 !important;
}

.stDataFrame tr[data-category="Read"] select,
.stDataFrame tr[data-category="Read"] div,
.stDataFrame select[value="Read"] {
    color: #4c7bff !important;
    font-weight: 600 !important;
}

.stDataFrame tr[data-category="Information"] select,
.stDataFrame tr[data-category="Information"] div,
.stDataFrame select[value="Information"] {
    color: #4cd97b !important;
    font-weight: 600 !important;
}

.stDataFrame tr[data-category="Events"] select,
.stDataFrame tr[data-category="Events"] div,
.stDataFrame select[value="Events"] {
    color: #ff9e4c !important;
    font-weight: 600 !important;
}

.stDataFrame tr[data-category="Uncategorised"] select,
.stDataFrame tr[data-category="Uncategorised"] div,
.stDataFrame select[value="Uncategorised"] {
    color: #666666 !important;
    font-weight: 600 !important;
}

/* Direct styling for category select elements */
.stDataFrame .column-category select,
.stDataFrame [data-testid="column-Category"] select {
    font-size: 15px !important;
    border: none !important;
    background-color: transparent !important;
    width: 100% !important;
    -webkit-appearance: none !important;
    -moz-appearance: none !important;
    appearance: none !important;
    text-align: center !important;
    font-weight: 600 !important;
}

/* Make select options visible when dropdown is open */
select option {
    color: black !important;
    background-color: white !important;
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

.stDataFrame {
    border: 2px solid rgba(128, 0, 128, 0.5) !important;
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

def get_row_style_html():
    """Return CSS for styling table rows based on category"""
    return """
<style>
/* Create colored backgrounds for rows based on category text */
.stDataFrame tbody tr:nth-child(n) td:nth-child(5):contains("Action") ~ td,
.stDataFrame tbody tr:nth-child(n) td:nth-child(5):contains("Action") {
    background-color: rgba(255, 76, 76, 0.08) !important;
}

.stDataFrame tbody tr:nth-child(n) td:nth-child(5):contains("Read") ~ td,
.stDataFrame tbody tr:nth-child(n) td:nth-child(5):contains("Read") {
    background-color: rgba(76, 123, 255, 0.08) !important;
}

.stDataFrame tbody tr:nth-child(n) td:nth-child(5):contains("Information") ~ td,
.stDataFrame tbody tr:nth-child(n) td:nth-child(5):contains("Information") {
    background-color: rgba(76, 217, 123, 0.08) !important;
}

.stDataFrame tbody tr:nth-child(n) td:nth-child(5):contains("Events") ~ td,
.stDataFrame tbody tr:nth-child(n) td:nth-child(5):contains("Events") {
    background-color: rgba(255, 158, 76, 0.08) !important;
}
</style>
""" 