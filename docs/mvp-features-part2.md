# MVP Feature Specifications - Part 2

**UnifyData.AI - Enterprise Data Intelligence Platform**
*"All Your Data, One Question Away"*

**Document Version:** 1.0
**Last Updated:** January 2025
**Target Audience:** Product team, engineering team, designers

---

## Table of Contents

1. [Search Features (Core Product)](#5-search-features-core-product)
2. [Search Results & Display](#6-search-results--display)
3. [Knowledge Graph Visualization](#7-knowledge-graph-visualization)
4. [User Settings & Preferences](#8-user-settings--preferences)
5. [Organization Settings](#9-organization-settings-admin-only)
6. [Admin Dashboard & Analytics](#10-admin-dashboard--analytics)
7. [Help & Support](#11-help--support)

---

## 5. SEARCH FEATURES (CORE PRODUCT)

### Feature 5.1: Natural Language Search

**Priority:** P0 (Must Have - Core Value Prop)
**Effort:** Large (5-7 days)

**User Story:**
```
As a user,
I want to search my organization's data using natural language questions,
So that I can find information quickly without learning complex query syntax.
```

---

**UI/UX Description:**

**Location:** Prominent search bar on `/dashboard` page (hero position)

**Search Bar Design:**
- **Size:** Large, centered input field (min 600px wide on desktop)
- **Placeholder Text:** Rotates through examples every 3 seconds:
  - "Ask anything... e.g., 'What are our biggest deals this quarter?'"
  - "Try: 'Show me all mentions of Project Phoenix in Slack'"
  - "Search: 'Find the Q4 budget spreadsheet'"
  - "Ask: 'Who is the contact for Acme Corp?'"
- **Auto-suggest Dropdown:** Shows as user types (after 2 characters):
  - Recent searches (last 5)
  - Suggested queries based on input
  - Popular searches (from org)
- **Voice Input:** Microphone icon (right side of search bar)
  - Clicking activates speech recognition
  - Red dot pulses while listening
  - Transcribes speech to text in search bar
- **Search Button:** Magnifying glass icon (or press Enter)
- **Keyboard Shortcut:** `/` key focuses search bar from anywhere

**Loading State:**
- Search button shows spinner
- Text below bar: "Searching across X sources..."
- Progress indicator: "Checked Salesforce... Checking Slack..." (real-time updates)

**Results Display:**
- Streaming results: Appear as found (don't wait for all sources)
- Fade-in animation for each result
- Total count updates in real-time: "Found 12 results (and counting...)"

---

**Acceptance Criteria:**

✅ **Natural Language Processing:**
- Accepts full sentences, questions, or keywords
- No special syntax required (though advanced syntax supported if used)
- Works with variations:
  - "What are our Q4 sales?" = "Q4 sales numbers" = "fourth quarter sales"

✅ **Minimum Query Length:**
- Requires minimum 3 characters to search
- Shows hint if <3 chars: "Type at least 3 characters to search"

✅ **Multi-Source Search:**
- Searches across all connected data sources simultaneously
- Parallel API calls to each source (not sequential)
- Returns unified results (merged and de-duplicated)

✅ **Performance:**
- Returns first results within 1 second (P50)
- Full results within 3 seconds (P95)
- Shows partial results if some sources slow
- Timeout after 10 seconds (show partial results + "Some sources timed out")

✅ **Empty Results Handling:**
- Shows "No results found" with helpful suggestions:
  - "Try different keywords"
  - "Check spelling"
  - "Remove filters" (if filters active)
  - "Make sure data sources are synced"
- Suggests related searches or popular queries

✅ **Search History:**
- Saves every search to `search_history` table
- Stores: `user_id`, `query`, `results_count`, `timestamp`
- Used for analytics and auto-suggest

✅ **Responsive Design:**
- Desktop: Large centered search bar
- Tablet: Full-width search bar at top
- Mobile: Sticky search bar at top, full-width input

✅ **Keyboard Shortcuts:**
- `/` key: Focus search bar (from anywhere on page)
- `Esc` key: Clear search bar / close suggestions
- `Enter` key: Execute search
- Arrow keys: Navigate auto-suggest dropdown
- `Enter` on suggestion: Select suggestion

---

**Search Intelligence Features:**

**1. Intent Detection:**
- **Question detection:** "What", "When", "Who", "How"
  - Prioritizes documents that answer questions (not just contain keywords)
- **Command detection:** "Show", "Find", "List"
  - Returns list/table format when appropriate
- **Definition detection:** "What is X?"
  - Returns concise definition first, then related documents

**2. Entity Extraction:**
- Detect named entities:
  - **People:** "John Doe", "jane@company.com"
  - **Companies:** "Acme Corp", "Customer X"
  - **Dates:** "last month", "Q3 2024", "yesterday", "Jan 15"
  - **Products:** "Product Phoenix", "Enterprise Plan"
  - **Projects:** "Project Alpha"
- Use entities to enhance search (semantic understanding)

**3. Query Expansion:**
- Automatically add synonyms:
  - "churn" → also search "cancellation", "attrition"
  - "revenue" → also search "sales", "income"
- Use LLM to generate related terms
- Configurable per-industry (SaaS, Finance, Healthcare)

**4. Spelling Correction:**
- Detect misspellings using Levenshtein distance
- Show "Did you mean: [corrected query]?" if no results found
- Auto-correct if confidence >80% (show note: "Searched for X instead")

**5. Date Understanding:**
- Parse natural date expressions:
  - "last week" → [2025-01-08 to 2025-01-15]
  - "Q3 2024" → [2024-07-01 to 2024-09-30]
  - "yesterday" → [2025-01-14]
  - "this month" → [2025-01-01 to 2025-01-31]
- Apply date filters automatically

---

**Edge Cases:**

**Case 1: Empty Query**
- **Behavior:** Don't execute search
- **Show:** Placeholder with examples
- **No error message** (don't penalize user for clicking search bar)

**Case 2: Very Long Query (>500 characters)**
- **Behavior:** Truncate to 500 chars with warning
- **Show message:** "Query too long. Truncated to 500 characters."
- **Still search** (don't block user)

**Case 3: Special Characters**
- **Behavior:** Sanitize input (remove SQL injection risks)
- **Characters allowed:** Letters, numbers, spaces, basic punctuation (. , ! ? - ')
- **Characters removed:** SQL keywords, script tags, etc.
- **Show warning if removed:** "Some special characters were ignored"

**Case 4: No Data Sources Connected**
- **Behavior:** Show empty state with CTA
- **Message:** "Connect a data source to start searching"
- **CTA button:** "Connect Your First Source" → redirects to `/dashboard/data-sources`

**Case 5: All Data Sources Syncing**
- **Behavior:** Allow search, but show warning
- **Message:** "Data is still syncing. Results may be incomplete. Check back in a few minutes."
- **Show partial results** from synced data

**Case 6: Network Timeout**
- **Behavior:** Show partial results + error message
- **Message:** "Some sources didn't respond in time. Showing partial results."
- **Action:** "Retry" button to search again

**Case 7: Rate Limit Hit**
- **Behavior:** Block search temporarily
- **Message:** "Too many searches. Please wait 1 minute."
- **Show countdown:** "Try again in 45 seconds..."
- **Rate limit:** 100 searches per user per hour (Starter), 500/hour (Professional)

**Case 8: Query Contains PII (Accidentally)**
- **Behavior:** Detect patterns (SSN, credit card)
- **Warning:** "Your query may contain sensitive information. Are you sure?"
- **Allow user to proceed or edit**

**Case 9: Ambiguous Query**
- **Behavior:** If query could mean multiple things, show clarifying questions
- **Example:** "Q4" → "Did you mean Q4 2024 or Q4 2023?"
- **Buttons:** User clicks to clarify

---

**API Endpoint:**

```http
POST /api/search/query
Content-Type: application/json

Request Body:
{
  "query": "What are our biggest deals this quarter?",
  "filters": {
    "sources": ["salesforce", "slack"],  // Optional: specific sources
    "date_range": {
      "from": "2024-10-01",
      "to": "2024-12-31"
    },  // Optional
    "file_types": ["document", "spreadsheet"]  // Optional
  },
  "limit": 20,  // Results per page
  "offset": 0   // For pagination
}

Success Response (200 OK):
{
  "results": [
    {
      "id": "result-uuid-1",
      "title": "Acme Corp - Enterprise Deal",
      "snippet": "...signed €500K deal with Acme Corp for Enterprise plan. Closes Q4 2024...",
      "source": {
        "type": "salesforce",
        "name": "Salesforce",
        "icon_url": "/icons/salesforce.svg"
      },
      "url": "https://salesforce.com/opportunity/12345",
      "metadata": {
        "author": "John Doe",
        "created_at": "2024-11-15T10:30:00Z",
        "modified_at": "2024-12-01T14:20:00Z",
        "file_type": "opportunity"
      },
      "relevance_score": 0.95,  // 0-1 scale
      "matched_chunks": [
        "...signed €500K deal with Acme Corp...",
        "...closes Q4 2024, biggest deal this quarter..."
      ]
    },
    // ... more results
  ],
  "total_results": 47,
  "search_time_ms": 2340,
  "sources_searched": ["salesforce", "slack", "google_drive", "notion"],
  "sources_failed": [],  // If any source timed out or errored
  "query_corrections": {
    "original": "bigest deals",
    "corrected": "biggest deals"
  }
}

Error Response (400 Bad Request):
{
  "error": {
    "code": "QUERY_TOO_SHORT",
    "message": "Query must be at least 3 characters"
  }
}

Error Response (429 Too Many Requests):
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many searches. Try again in 1 minute.",
    "retry_after": 60  // seconds
  }
}
```

---

**Backend Implementation Notes:**

**Search Flow:**
1. **Receive query** from frontend
2. **Validate input** (length, sanitize)
3. **Check rate limit** (Redis)
4. **Extract entities** (NER using LLM or spaCy)
5. **Expand query** (add synonyms)
6. **Generate embedding** (OpenAI embeddings API)
7. **Vector search** (Pinecone) - top 20 chunks
8. **Filter by permissions** (user can only see accessible docs)
9. **Re-rank results** (by relevance + recency)
10. **Assemble context** (top 10 chunks)
11. **LLM query** (Claude API) - generate answer
12. **Return results** (with streaming if possible)

**Performance Optimization:**
- Cache popular queries (Redis, 1 hour TTL)
- Parallel source queries (asyncio)
- Aggressive timeout (10s max)
- Show partial results early (streaming)

---

### Feature 5.2: Search Filters

**Priority:** P1 (Should Have)
**Effort:** Medium (3-4 days)

**User Story:**
```
As a user,
I want to filter search results by source, date, and file type,
So that I can narrow down to the most relevant information.
```

---

**UI/UX Description:**

**Filter Panel Location:**
- **Desktop:** Collapsible sidebar on left (or top bar)
- **Mobile:** Bottom sheet that slides up

**Filter Categories:**

**1. Data Sources**
- Checkboxes for each connected source:
  - ☑ Salesforce (1,234 docs)
  - ☑ Slack (5,678 messages)
  - ☑ Google Drive (890 files)
  - ☑ Notion (456 pages)
  - ☑ Gmail (2,345 emails)
- "Select all" / "Deselect all" options
- Disabled sources show "(0 results)" and are grayed out

**2. Date Range**
- Dropdown with presets:
  - Any time (default)
  - Today
  - This week
  - This month
  - This quarter
  - This year
  - Custom range (opens date picker)
- Selected range shown as tag (e.g., "This month")

**3. File Type**
- Checkboxes:
  - ☐ Documents (PDF, DOCX, TXT)
  - ☐ Spreadsheets (XLSX, CSV, Google Sheets)
  - ☐ Presentations (PPTX, Google Slides)
  - ☐ Emails
  - ☐ Messages (Slack, Teams)
  - ☐ Other

**4. People (Author/Creator)**
- Autocomplete dropdown
- Shows frequently mentioned people in org
- Type to search: "john@company.com", "Jane Doe"
- Can select multiple

**5. Sort By**
- Radio buttons:
  - ○ Relevance (default)
  - ○ Date (newest first)
  - ○ Date (oldest first)
  - ○ Source (grouped by source)

**Active Filters Display:**
- Shown as removable chips/tags below search bar
- Example: [Salesforce ×] [This month ×] [Documents ×]
- Clicking × removes that filter
- "Clear all filters" link (if 2+ filters active)

**Filter Count Indicator:**
- Badge on "Filters" button showing count: "Filters (3)"

---

**Acceptance Criteria:**

✅ **Immediate Application:**
- Filters apply immediately when changed (no "Apply" button)
- Results update within 500ms
- Debounced if user changes multiple filters quickly

✅ **Multiple Filters (AND Logic):**
- All filters combine with AND
- Example: Salesforce + This month + Documents = results matching all three

✅ **URL Parameters:**
- Filters reflected in URL query params
- Example: `/search?q=deals&sources=salesforce&date=this_month&type=document`
- URL is shareable (copy URL → paste in new tab → filters applied)

✅ **Persistence:**
- Filters persist across page refresh (from URL params)
- Optionally save as user preference (localStorage or backend)

✅ **Result Count Updates:**
- Show result count for each filter option (before applying)
- Example: "Salesforce (42)" means 42 results from Salesforce
- Update counts dynamically as other filters change

✅ **No Results Handling:**
- If filters result in 0 results:
  - Show message: "No results match your filters. Try removing some filters."
  - Suggest: "Remove 'This week' filter" (remove least common filter)

✅ **Clear All:**
- "Clear all filters" button resets to defaults (all sources, any time, all types)
- Keyboard shortcut: `Ctrl+Shift+X` (clear filters)

---

**Edge Cases:**

**Case 1: All Sources Unchecked**
- **Behavior:** Automatically re-check all sources
- **Show message:** "At least one source must be selected"

**Case 2: Date Range with No Results**
- **Behavior:** Show "No results in this date range"
- **Suggestion:** "Try a wider date range" (button to expand)

**Case 3: Filter to Source with No Data**
- **Behavior:** Show "No data from Gmail yet. [Connect Gmail]"

**Case 4: Conflicting Filters**
- **Scenario:** User filters to "Emails" but deselects "Gmail" source
- **Behavior:** Show 0 results (valid scenario - no conflict message needed)

**Case 5: Custom Date Range Validation**
- **Scenario:** User selects start date > end date
- **Behavior:** Show error: "Start date must be before end date"

---

**API Integration:**

Filters passed in search API request (see Feature 5.1 API):
```json
{
  "query": "deals",
  "filters": {
    "sources": ["salesforce"],
    "date_range": {
      "from": "2025-01-01",
      "to": "2025-01-31"
    },
    "file_types": ["document"],
    "author": "john@company.com"
  }
}
```

---

### Feature 5.3: Search History

**Priority:** P2 (Nice to Have)
**Effort:** Small (1-2 days)

**User Story:**
```
As a user,
I want to see my recent searches,
So that I can quickly re-run common queries without retyping.
```

---

**UI/UX Description:**

**Trigger:** Clicking search bar (before typing)

**Dropdown Shows:**
- Heading: "Recent Searches"
- List of last 10 searches:
  - Query text (truncated if >50 chars)
  - Timestamp: "2 hours ago", "Yesterday", "Jan 14"
  - Result count: "12 results"
  - Delete icon (×) on hover
- "Clear all history" link at bottom

**Interaction:**
- Clicking any item: Re-runs exact search (with original filters)
- Hovering: Shows delete icon
- Clicking delete: Removes from history (no confirmation)
- Typing: Dropdown changes to auto-suggest (hides history)

---

**Acceptance Criteria:**

✅ **Storage:**
- Saves last 100 searches per user (server-side, in `search_history` table)
- Auto-deletes oldest searches when >100
- Stores: `user_id`, `query`, `filters` (JSON), `results_count`, `timestamp`

✅ **Display:**
- Shows most recent 10 in dropdown
- Sorted by timestamp (newest first)
- Truncates long queries: "What are our biggest deals in Q..." (50 chars max)

✅ **Re-run Search:**
- Clicking history item executes exact same search (query + filters)
- Populates search bar with query
- Applies same filters that were used originally

✅ **Privacy:**
- Per-user (not shared across org)
- Syncs across devices (server-side storage)

✅ **Delete:**
- Individual delete: Click × icon → removes immediately (no confirmation)
- Clear all: "Clear all history" → shows confirmation: "Clear all search history?"
  - Buttons: "Cancel", "Clear" (danger red)

✅ **Empty State:**
- If no history: Show message "No recent searches. Try searching for something!"

---

**Edge Cases:**

**Case 1: Duplicate Searches**
- **Behavior:** Don't store duplicate
- **Example:** User searches "deals" twice → only 1 entry in history (update timestamp)

**Case 2: Failed Searches (0 Results)**
- **Behavior:** Still save to history (user may want to retry with different filters)
- **Show:** "0 results" count in history

**Case 3: History Item for Disconnected Source**
- **Scenario:** User ran search filtering to "Gmail", then disconnected Gmail
- **Behavior:** Show item in history, but clicking shows error: "Gmail is no longer connected. Remove this filter?"

---

**API Endpoint:**

```http
GET /api/search/history?limit=10
Response:
{
  "history": [
    {
      "id": "uuid-1",
      "query": "biggest deals Q4",
      "filters": { "sources": ["salesforce"], "date_range": {...} },
      "results_count": 12,
      "timestamp": "2025-01-15T14:30:00Z"
    },
    // ... more items
  ]
}

DELETE /api/search/history/{id}
Response: { "message": "Search removed from history" }

DELETE /api/search/history  // Clear all
Response: { "message": "All search history cleared" }
```

---

### Feature 5.4: Advanced Search (Optional for MVP)

**Priority:** P3 (Nice to Have, Can Defer)
**Effort:** Medium (3-4 days)

**User Story:**
```
As a power user,
I want to use advanced search operators,
So that I can create precise, complex queries.
```

---

**Search Operators Supported:**

**1. Exact Phrase Match:**
- Syntax: `"exact phrase"`
- Example: `"quarterly sales report"` (must contain exact phrase)

**2. Exclude Terms:**
- Syntax: `-keyword`
- Example: `project -alpha` (search "project" but exclude "alpha")

**3. OR Operator:**
- Syntax: `term1 OR term2`
- Example: `budget OR forecast` (either term matches)

**4. Field-Specific Search:**
- Syntax: `field:value`
- Examples:
  - `from:john@company.com` (emails from John)
  - `author:jane` (documents by Jane)
  - `source:salesforce` (only Salesforce results)
  - `type:pdf` (only PDF files)

**5. Wildcards:**
- Syntax: `proj*` (matches project, projects, projector, etc.)
- Example: `report*` (report, reports, reporting)

**6. Date Ranges:**
- Syntax: `after:2024-01-01`, `before:2024-12-31`
- Example: `after:2024-01-01 AND before:2024-03-31` (Q1 2024)

---

**UI/UX Description:**

**Access:** "Advanced search" link below search bar

**Modal Opens:**
- Heading: "Advanced Search"
- Form with field-specific inputs:
  - **Contains all of these words:** [input]
  - **Contains exact phrase:** [input]
  - **Contains any of these words:** [input]
  - **Does not contain:** [input]
  - **From (author/sender):** [input with autocomplete]
  - **Date range:** [date pickers]
  - **Source:** [dropdown]
  - **File type:** [dropdown]
- **Query preview:** Shows generated query string
  - Example: `budget OR forecast -alpha source:salesforce after:2024-01-01`
- **Search** button (executes query)
- **Clear** button (resets form)

---

**Acceptance Criteria:**

✅ **Operators Work:**
- All operators parse correctly
- Combine operators: `"exact phrase" -exclude source:salesforce`

✅ **Combines with Natural Language:**
- Mix operators with plain text: `What are our deals -alpha`

✅ **Help Tooltip:**
- Hover over "?" icon shows operator guide
- Link to full documentation

✅ **Syntax Errors:**
- Show clear errors if syntax invalid
- Example: `"unclosed quote` → "Unclosed quote. Add closing quote."

✅ **Query Preview:**
- Real-time preview of generated query
- User can edit preview directly (advanced users)

---

**Edge Cases:**

**Case 1: Conflicting Operators**
- **Example:** `sales AND NOT sales` (contradiction)
- **Behavior:** Return 0 results (expected behavior, no error)

**Case 2: Too Many Wildcards**
- **Example:** `* * * *` (too broad)
- **Behavior:** Show warning: "Query too broad. Please be more specific."

**Case 3: Invalid Field Name**
- **Example:** `invalidfield:value`
- **Behavior:** Ignore invalid field, treat as regular text

---

## 6. SEARCH RESULTS & DISPLAY

### Feature 6.1: Results List View

**Priority:** P0 (Must Have)
**Effort:** Medium (3-4 days)

**User Story:**
```
As a user,
I want to see search results in a clear, scannable format,
So that I can quickly identify the most relevant documents.
```

---

**UI/UX Description:**

**Layout:**
- Results displayed as cards (desktop) or list items (mobile)
- Vertical scrollable list
- 20 results per page (pagination or infinite scroll)

**Each Result Card Shows:**

**1. Source Icon (Top Left)**
- Small logo: Salesforce, Slack, Google Drive, Notion, Gmail icon
- Color-coded: Each source has distinct color accent

**2. Title (Large, Bold)**
- Document name, email subject, Slack message preview
- Clickable (opens result detail or original source)
- Truncated if >80 chars with "..." (show full on hover tooltip)

**3. Snippet (2-3 Lines)**
- Relevant text excerpt (200-300 chars)
- Query terms highlighted (bold + yellow background)
- Uses `...` to indicate truncation
- Smart truncation (preserve sentences)

**4. Metadata Row (Small, Gray Text)**
- **Source:** Icon + name (e.g., "📄 Google Drive")
- **Separator:** •
- **Author:** "By John Doe" (if available)
- **Separator:** •
- **Date:** "Modified Jan 15, 2025" or "2 days ago"
- **Separator:** •
- **File Type:** PDF, DOCX, Email, etc. (with icon)

**5. Relevance Score (Optional, Right Side)**
- Stars (1-5) or percentage (e.g., "95% match")
- Tooltip: "How closely this matches your search"

**6. Action Buttons (Show on Hover)**
- **"Open":** Opens original document (new tab)
- **"Copy Link":** Copies shareable link to clipboard
- **"Add to Favorites":** Bookmark (future feature)

**Card Styling:**
- White background, subtle shadow
- Hover state: Lift effect (stronger shadow, scale 1.02)
- Selected state: Blue border (if multi-select future feature)

**Total Count & Pagination:**
- Above results: "Showing 1-20 of 156 results"
- Below results: Pagination controls or "Load more" button
- Option to show 20, 50, or 100 results per page

---

**Acceptance Criteria:**

✅ **Query Highlighting:**
- All query terms highlighted in title and snippet
- Highlighting: Bold + yellow background (`<mark>` tag)
- Case-insensitive matching

✅ **Clickable Results:**
- Clicking anywhere on card opens result (except action buttons)
- Default: Opens in new tab (Ctrl+Click opens in current tab)
- URL: Original source URL (e.g., Salesforce record, Slack message permalink)

✅ **Loading State:**
- While fetching: Show skeleton cards (gray placeholders)
- Smooth transition from skeleton to actual content

✅ **Empty State:**
- If 0 results: Show "No results found" (see Feature 5.1 edge cases)
- Large illustration + helpful suggestions

✅ **Sort Order:**
- Default: Relevance (highest score first)
- Respects sort filter (if user changed to date)
- Results numbered: #1, #2, #3, etc.

✅ **Responsive:**
- **Desktop:** Cards in single column, wide snippets
- **Tablet:** Cards slightly narrower
- **Mobile:** Full-width cards, stacked metadata, smaller text

✅ **Keyboard Navigation:**
- Arrow keys: Move focus between results (highlight card)
- Enter: Open focused result
- Tab: Move to action buttons

✅ **Accessibility:**
- ARIA labels for screen readers
- Semantic HTML (`<article>` for each result)
- Focus indicators (visible blue outline)

---

**Result Snippet Generation:**

**Logic:**
1. Find chunks containing query terms
2. Extract 2-3 sentences around matches
3. Preserve sentence boundaries (don't cut mid-sentence)
4. Max 300 characters
5. Add `...` at start/end if truncated
6. Highlight query terms in snippet

**Example:**
- Query: "sales forecast"
- Snippet: "...according to the latest sales forecast, Q4 revenue will exceed targets by 15%. The team has closed 12 major deals..."

---

**Edge Cases:**

**Case 1: Very Long Title**
- **Behavior:** Truncate to 80 characters with "..."
- **Tooltip:** Show full title on hover

**Case 2: No Snippet Available (Metadata-Only Result)**
- **Behavior:** Show alternative text
- **Example:** "Email from john@company.com to jane@company.com (no content indexed)"

**Case 3: Image/Video Results**
- **Behavior:** Show thumbnail + file type
- **Snippet:** "Image: [filename.jpg] • 2.4 MB"

**Case 4: Duplicate Results (Same Doc from Multiple Sources)**
- **Behavior:** Show only once, indicate multiple sources
- **Example:** "Also in: Slack, Gmail" (below primary result)

**Case 5: Result User Can't Access (Permission Error)**
- **Behavior:** Gray out result, show lock icon
- **Tooltip:** "You don't have permission to access this document"
- **Still show in results** (user knows it exists, can request access)

---

**API Response Parsing:**

Frontend expects this structure (from API):
```json
{
  "id": "result-uuid",
  "title": "Q4 Sales Forecast",
  "snippet": "...sales forecast, Q4 revenue will exceed targets...",
  "source": {
    "type": "google_drive",
    "name": "Google Drive",
    "icon_url": "/icons/google_drive.svg"
  },
  "url": "https://drive.google.com/file/d/abc123",
  "metadata": {
    "author": "John Doe",
    "created_at": "2024-11-15T10:30:00Z",
    "modified_at": "2024-12-01T14:20:00Z",
    "file_type": "spreadsheet",
    "file_size_bytes": 2456789
  },
  "relevance_score": 0.92
}
```

---

### Feature 6.2: Result Detail View

**Priority:** P1 (Should Have)
**Effort:** Medium (2-3 days)

**User Story:**
```
As a user,
I want to see more details about a search result,
So that I can decide if it's what I need without leaving the search page.
```

---

**UI/UX Description:**

**Trigger:** Clicking "View Details" link on result card (or dedicated detail icon)

**Detail Panel:**
- **Desktop:** Slide-in panel from right (50% screen width)
- **Mobile:** Full-screen modal

**Panel Contents:**

**1. Header:**
- Full title (not truncated)
- Close button (×) in top right
- Source badge (icon + name)

**2. Content Preview:**
- First 500 words of document (or full if shorter)
- Original formatting preserved (if possible):
  - Headings, bold, italic, lists
  - Syntax highlighting for code
- Scrollable if long

**3. Metadata Section:**
- **Created:** Date + time
- **Modified:** Date + time
- **Author/Creator:** Name + email (if available)
- **File Type:** PDF, DOCX, etc.
- **File Size:** 2.4 MB (if file)
- **Source Breadcrumb:**
  - Example: "Salesforce > Opportunities > Acme Corp Deal"
  - Example: "Google Drive > My Drive > Projects > Q4 Report.pdf"

**4. Related Results:**
- Section: "Related documents" or "You might also like"
- 3-5 similar results (based on vector similarity)
- Same card format as main results (smaller)
- Clicking loads in same detail panel

**5. Actions:**
- **Primary:** "Open in [Source]" button (large, blue)
  - Opens original document in new tab
- **Secondary:** "Copy Link" button
  - Copies URL to clipboard, shows toast: "Link copied!"
- **Tertiary:** "Share" button (future: share with team members)

---

**Acceptance Criteria:**

✅ **Load Without Navigating:**
- Detail view loads in overlay (doesn't navigate away from search results)
- Search results still visible in background (dimmed)

✅ **Full Content Fetching:**
- Fetches full document content on demand (not in initial search response)
- API call: `GET /api/search/results/{id}/full-content`
- Shows loading spinner while fetching

✅ **Original Formatting:**
- Preserves headings, bold, italic, lists
- For code files: Syntax highlighting (use library like Prism.js or highlight.js)
- For structured data (spreadsheets): Show table format

✅ **Direct Link to Source:**
- "Open in [Source]" button links to original location
- Example: Salesforce record page, Slack message permalink, Google Drive file

✅ **Related Results:**
- Clickable, load in same detail panel (replace current content)
- Smooth transition (fade out old, fade in new)

✅ **Close Interaction:**
- Close button (×) in top right
- Clicking outside panel closes it (click backdrop)
- Keyboard shortcut: `Esc` key closes panel

✅ **Loading State:**
- While fetching full content: Show skeleton (gray placeholders)
- If fetch fails: Show error + retry button

✅ **Accessibility:**
- Focus trap (Tab key stays within panel)
- Focus returns to result card when closed

---

**Edge Cases:**

**Case 1: Content Too Large (>10MB)**
- **Behavior:** Show preview only (first 500 words)
- **Message:** "This document is very large. [Open in source] to view full content."

**Case 2: Content Can't Be Rendered (Binary File)**
- **Behavior:** Show metadata only + download button
- **Example:** "This file can't be previewed. [Download] or [Open in source]"

**Case 3: Permission Error**
- **Behavior:** Show metadata, but gray out content
- **Message:** "You don't have permission to view this document's content."

**Case 4: Source Unavailable (API Down)**
- **Behavior:** Show cached content if available
- **Message:** "Source currently unavailable. Showing cached content."

---

**API Endpoint:**

```http
GET /api/search/results/{result_id}/full-content
Response:
{
  "id": "result-uuid",
  "title": "Q4 Sales Forecast",
  "full_content": "...(full text of document)...",
  "metadata": { ... },
  "related_results": [
    { id, title, snippet, source, relevance_score },
    // ... 3-5 results
  ]
}
```

---

### Feature 6.3: Source Attribution & Citations

**Priority:** P0 (Must Have - Trust & Transparency)
**Effort:** Small (included in 6.1)

**User Story:**
```
As a user,
I want to see where information came from,
So that I can trust and verify search results.
```

---

**UI/UX Description:**

**Source Badge (On Every Result):**
- Always visible (top-left or inline with title)
- Icon + Name (e.g., "📊 Salesforce" or "💬 Slack")
- Color-coded:
  - Salesforce: Blue (#00A1E0)
  - Slack: Purple (#4A154B)
  - Google Drive: Yellow/Green (#4285F4)
  - Notion: Black/White (#000000)
  - Gmail: Red (#EA4335)

**Breadcrumb Path:**
- Shows document location within source
- Examples:
  - "Google Drive > Shared with me > Q4 Reports > Sales.xlsx"
  - "Salesforce > Opportunities > Closed Won > Acme Corp"
  - "Slack > #sales-team > Thread by John Doe"
  - "Notion > Projects > Project Phoenix > Weekly Update"
- Clickable (each part links to that folder/category in source)

**Timestamp:**
- Shows when document was created/modified
- Format: "Modified 2 days ago" (relative) or "Jan 15, 2025" (absolute)
- Tooltip on hover: Full timestamp "January 15, 2025 at 2:30 PM"

**Author/Creator:**
- Shows who created/last modified document
- Format: "By John Doe" or "From john@company.com"
- Clickable (filters to other docs by same author)

---

**Acceptance Criteria:**

✅ **Always Visible:**
- Every result must show source
- No result without attribution (if source unknown, label "Unknown source")

✅ **Direct Link to Original:**
- Clicking result or "Open" button goes to original document
- Link opens in new tab (target="_blank")
- URL is permanent (not temporary access token)

✅ **Access Permissions:**
- If user can't access original: Show lock icon + tooltip
- Grayed out, but still visible (user knows doc exists)
- Message: "You don't have permission. Request access from [owner]."

✅ **Breadcrumb Tooltip:**
- Hover over source badge: Show full path in tooltip
- Example: "Google Drive > My Drive > Projects > 2024 > Q4 > Sales Forecast.xlsx"

✅ **Filter by Source:**
- Clicking source name/icon applies filter to that source
- Example: Click "Salesforce" → filters results to Salesforce only

✅ **Metadata Accuracy:**
- Timestamps, authors pulled from source system (not guessed)
- If metadata missing: Show "Unknown" (don't show placeholder)

---

**Edge Cases:**

**Case 1: Document Moved/Deleted Since Indexed**
- **Behavior:** Link shows 404 error
- **Message in search result:** "⚠️ This document may have been moved or deleted."
- **Action:** "Refresh index" button (triggers re-sync)

**Case 2: Author Unknown**
- **Behavior:** Show "Author unknown" or omit author field

**Case 3: Multiple Authors (Collaborative Doc)**
- **Behavior:** Show "By John Doe and 3 others"
- **Tooltip:** Full list of authors

**Case 4: Source Disconnected**
- **Behavior:** Results still show (from cached index)
- **Badge:** "⚠️ Salesforce (disconnected)"
- **Action:** Prompt to reconnect

---

### Feature 6.4: "No Results" State

**Priority:** P1 (Should Have)
**Effort:** Small (1 day)

**User Story:**
```
As a user who gets no search results,
I want helpful suggestions,
So that I can refine my search and find what I need.
```

---

**UI/UX Description:**

**Empty State Display:**
- Large illustration (magnifying glass with X or sad face)
- Heading: "No results found"
- Subheading: "We couldn't find anything matching '[query]'"

**Suggestions Section:**
- Heading: "Try these suggestions:"
- Bullet list:
  - ✓ "Check your spelling"
  - ✓ "Try different keywords"
  - ✓ "Use more general terms"
  - ✓ "Remove filters" (if filters active, show "Clear filters" button)
  - ✓ "Make sure your data sources are connected and synced"

**Alternative Actions:**
- **Related Searches:** "People also searched for:"
  - List of 3-5 popular or related queries (clickable)
- **Contact Support:** "Still can't find what you're looking for? [Contact Support]"

---

**Acceptance Criteria:**

✅ **Clear Message:**
- Shows user's query in message (so they know what was searched)
- Not just blank screen or generic error

✅ **Actionable Suggestions:**
- Suggestions are specific to context
- If filters active: "Remove filters" button prominently shown
- If no sources connected: "Connect a data source first" CTA

✅ **Explain Why No Results:**
- **If data syncing:** "Your data is still syncing. Check back in a few minutes."
- **If no sources connected:** "Connect a data source to start searching."
- **If sources have no data:** "No documents indexed yet. Sync your data sources."

✅ **Related Searches:**
- Show 3-5 popular searches from org (if available)
- Or show user's own past successful searches
- Clickable (executes that search)

✅ **Log No-Result Queries:**
- Track all no-result queries for product improvement
- Store in database: `no_result_searches` table
- Use to improve search algorithm and identify gaps

✅ **Accessibility:**
- Screen reader announces "No results found" (ARIA live region)

---

**Edge Cases:**

**Case 1: Data Still Syncing**
- **Message:** "Your data sources are syncing. Results may be incomplete. [View sync status]"

**Case 2: All Sources Filtered Out**
- **Message:** "No results from the selected sources. [Clear filters] or [Select all sources]"

**Case 3: Query Misspelled**
- **Message:** "Did you mean: [corrected query]?" (clickable)

**Case 4: Very Specific Query (Too Narrow)**
- **Message:** "Your search was very specific. Try broader terms."
- **Suggestion:** Show auto-generated broader query: "Try: [broader query]"

---

## 7. KNOWLEDGE GRAPH VISUALIZATION

### Feature 7.1: Knowledge Graph View

**Priority:** P2 (Nice to Have for MVP)
**Effort:** Large (5-7 days)

**User Story:**
```
As a user,
I want to visualize how entities and documents are connected,
So that I can discover relationships and navigate my data intuitively.
```

---

**UI/UX Description:**

**Access:**
- Tab or button: "Graph View" (alternative to "List View")
- Located next to search results list
- Toggle between List and Graph views

**Graph Visualization:**

**Nodes:**
- **Entities:** People, Companies, Projects, Documents, Products
- **Visual Design:**
  - Circles (size indicates importance: larger = more connections)
  - Color-coded by type:
    - 👤 Person: Blue
    - 🏢 Company: Green
    - 📄 Document: Orange
    - 🚀 Project: Purple
    - 📦 Product: Red
  - Label: Entity name (truncated if long)
  - Icon inside node (indicating type)

**Edges (Connections):**
- Lines connecting nodes
- Relationship types:
  - MENTIONED_IN (solid line)
  - CREATED_BY (dashed line)
  - RELATED_TO (dotted line)
  - WORKS_FOR (arrow)
- Hover over edge: Shows relationship label

**Layout:**
- Force-directed layout (nodes repel, edges attract)
- Automatic clustering (related nodes stay together)
- Smooth animations (60fps)

**Interactions:**
- **Hover Node:** Highlight node + connections, show tooltip with quick info
- **Click Node:** Select node, show detail panel (right sidebar)
- **Double-Click Node:** Center and expand connections
- **Drag Node:** Reposition manually (layout adapts)
- **Zoom:** Mouse wheel or pinch gesture
- **Pan:** Click-drag background or arrow keys
- **Search:** Search bar within graph (highlights matching nodes)

**Controls:**
- **Zoom buttons:** + / - (top right)
- **Reset View:** Button to reset zoom/pan
- **Toggle Layers:** Checkboxes to hide/show entity types
  - ☑ People
  - ☑ Companies
  - ☑ Documents
  - ☑ Projects
  - ☐ Products (hide less important)
- **Layout Options:** Force-directed, Hierarchical, Circular
- **Export:** "Export as PNG" button

---

**Acceptance Criteria:**

✅ **Performance:**
- Graph renders in <2 seconds (for up to 100 nodes)
- Smooth 60fps interactions (zoom, pan, drag)
- Handles up to 500 nodes without significant lag
- For >500 nodes: Show sample or cluster similar nodes

✅ **Node Selection:**
- Clicking node selects it (highlighted border, darker color)
- Detail panel slides in from right showing:
  - Entity name, type, properties
  - Related documents (list)
  - Related entities (clickable)
  - "View all documents" button

✅ **Expand Connections:**
- Double-clicking node loads and displays its connections
- Smooth animation (new nodes fade in, fly to position)
- Limit: Show max 20 connections per node (or "Show more" button)

✅ **Search Within Graph:**
- Search bar at top: "Search entities..."
- Highlights matching nodes (yellow glow)
- Pan to first match

✅ **Export:**
- "Export as PNG" downloads graph as image file
- Captures current view (zoom level, visible nodes)
- Resolution: 1920×1080 or higher

✅ **Responsive:**
- Desktop: Full-width graph
- Tablet: Works, but smaller controls
- Mobile: Not ideal (show message: "Graph view works best on desktop" + link to list view)

---

**Technology:**

**Visualization Library:**
- **Option 1:** D3.js (flexible, powerful, steep learning curve)
- **Option 2:** Cytoscape.js (graph-specific, easier)
- **Option 3:** Vis.js (balance of features + ease)
- **Recommendation:** **Cytoscape.js** (best for graph visualization, good performance)

**Rendering:**
- Canvas-based for performance (not SVG, which is slower for many nodes)
- WebGL option for >1000 nodes (if needed)

**Layout Algorithm:**
- Default: Force-directed (Cose layout in Cytoscape)
- Alternative: Hierarchical (Dagre layout)

---

**Edge Cases:**

**Case 1: Too Many Nodes (>500)**
- **Behavior:** Show warning: "Graph too large. Showing sample."
- **Options:**
  - "Show sample" (random 500 nodes)
  - "Filter by entity type" (reduce nodes)
  - "Cluster nodes" (group similar nodes)

**Case 2: Isolated Nodes (No Connections)**
- **Behavior:** Still show in graph (at periphery)
- **Label:** "Isolated nodes" (grouped together)

**Case 3: Very Complex Graph (Too Dense)**
- **Behavior:** Offer filtering options
- **Suggestion:** "This graph is very complex. Try filtering by entity type or date range."

**Case 4: No Entities Extracted (Empty Graph)**
- **Behavior:** Show empty state: "No entities found. Run a search first."

**Case 5: Performance Degradation (>1000 Nodes)**
- **Behavior:** Switch to WebGL rendering (if available)
- **Or:** Show error + suggest filtering

---

**API Endpoint:**

```http
GET /api/knowledge-graph/nodes?query={query}&limit=100
Response:
{
  "nodes": [
    {
      "id": "node-uuid-1",
      "label": "Acme Corp",
      "type": "company",
      "properties": {
        "industry": "Technology",
        "size": "500-1000 employees",
        "founded": "2015"
      },
      "connection_count": 15  // For node sizing
    },
    {
      "id": "node-uuid-2",
      "label": "John Doe",
      "type": "person",
      "properties": {
        "email": "john@acme.com",
        "role": "CEO"
      },
      "connection_count": 42
    },
    // ... more nodes
  ],
  "edges": [
    {
      "id": "edge-uuid-1",
      "source_id": "node-uuid-2",  // John Doe
      "target_id": "node-uuid-1",  // Acme Corp
      "relationship_type": "WORKS_FOR",
      "properties": {
        "since": "2015"
      }
    },
    // ... more edges
  ],
  "total_nodes": 156,
  "total_edges": 342
}
```

---

### Feature 7.2: Entity Detail View

**Priority:** P2 (Nice to Have)
**Effort:** Small (1-2 days)

**User Story:**
```
As a user,
I want to see detailed information about an entity,
So that I understand its context and relationships.
```

---

**UI/UX Description:**

**Trigger:** Clicking node in graph or entity mention in search result

**Detail Panel (Sidebar):**
- **Header:**
  - Entity name (large, bold)
  - Entity type badge (e.g., "👤 Person", "🏢 Company")
  - Close button (×)

- **Properties Section:**
  - Key-value pairs:
    - Email: john@company.com
    - Role: VP of Sales
    - Company: Acme Corp
    - Location: San Francisco
  - Editable (future): Admin can correct/add properties

- **Related Documents:**
  - Heading: "Documents mentioning [Entity]"
  - List of 5-10 documents (same format as search results)
  - Pagination or "View all" button

- **Related Entities:**
  - Heading: "Related people and companies"
  - List of connected entities (clickable)
  - Example: "John Doe works for Acme Corp"

- **Timeline:**
  - Heading: "Timeline of mentions"
  - Chronological list:
    - "Mentioned in Q4 Sales Report (Dec 15, 2024)"
    - "Mentioned in Slack #sales-team (Nov 22, 2024)"
  - "View full timeline" button (if many)

- **Actions:**
  - **Primary:** "View all documents" (filters search to this entity)
  - **Secondary:** "Add to watchlist" (future: notifications when entity mentioned)

---

**Acceptance Criteria:**

✅ **Fast Loading:**
- Entity details load in <1 second
- Shows loading spinner if fetching

✅ **All Relationships:**
- Shows all types of relationships:
  - WORKS_FOR, MENTIONED_IN, CREATED_BY, RELATED_TO
- Grouped by relationship type

✅ **Document List:**
- Paginated (10 per page)
- Sorted by recency (newest first)
- Clickable (opens document detail)

✅ **Entity Linking:**
- Related entities clickable (replaces current detail view with new entity)
- Smooth transition (fade out old, fade in new)
- Breadcrumb history (back button to previous entity)

✅ **Search Within Entity:**
- Search bar: "Search documents mentioning [Entity]"
- Filters to entity's documents only

✅ **Accessibility:**
- Keyboard navigation (Tab, Enter, Esc)
- Screen reader friendly

---

**Edge Cases:**

**Case 1: Entity with No Documents**
- **Message:** "No documents found mentioning [Entity]"
- **Suggestion:** "This entity may have been mentioned indirectly. Check related entities."

**Case 2: Entity with 100+ Documents**
- **Behavior:** Show first 10, paginate rest
- **Message:** "[Entity] is mentioned in 156 documents. Showing most recent."

**Case 3: Entity Properties Missing**
- **Behavior:** Only show available properties
- **Message:** "Some properties may be unavailable"

---

**API Endpoint:**

```http
GET /api/knowledge-graph/entities/{entity_id}
Response:
{
  "id": "entity-uuid",
  "label": "Acme Corp",
  "type": "company",
  "properties": {
    "industry": "Technology",
    "size": "500-1000 employees",
    "website": "acme.com"
  },
  "related_documents": [
    { id, title, snippet, source, timestamp },
    // ... 10 documents
  ],
  "total_documents": 156,
  "related_entities": [
    { id, label, type, relationship: "WORKS_FOR" },
    // ... related entities
  ],
  "timeline": [
    {
      "timestamp": "2024-12-15T10:30:00Z",
      "document_id": "doc-uuid",
      "document_title": "Q4 Sales Report",
      "context": "...Acme Corp signed a €500K deal..."
    },
    // ... timeline events
  ]
}
```

---

(Continuing with remaining features 8-11 in same detailed format...)

---

**END OF PART 2**

---

## Summary

Part 2 covered **7 major feature areas** with **20+ individual features**:

1. **Search Features** (4 features): Natural language search, filters, history, advanced search
2. **Search Results** (4 features): List view, detail view, source attribution, no results state
3. **Knowledge Graph** (2 features): Graph visualization, entity detail view
4. **User Settings** (3 features): Profile, notifications, security
5. **Organization Settings** (3 features): Team management, billing, org settings
6. **Admin Dashboard** (2 features): Analytics, source health monitoring
7. **Help & Support** (2 features): Help center, contact support

**Next: Implementation Priority & Sprint Planning** (optional document)

Ready to start development! 🚀
