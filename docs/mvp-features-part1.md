# MVP Feature Specifications - Part 1

**UnifyData.AI - Enterprise Data Intelligence Platform**
*"All Your Data, One Question Away"*

**Document Version:** 1.0
**Last Updated:** January 2025
**Target Audience:** Product team, engineering team, designers

---

## Table of Contents

1. [User Authentication & Registration](#1-user-authentication--registration)
2. [Onboarding Flow](#2-onboarding-flow-new-user)
3. [Data Source Connection](#3-data-source-connection-core-feature)
4. [Data Sync Management](#4-data-sync-management)

---

## 1. USER AUTHENTICATION & REGISTRATION

### Feature 1.1: User Registration (Sign Up)

**Priority:** P0 (Must Have)
**Effort:** Medium (3-4 days)

**User Story:**
```
As a new user,
I want to create an account with my email and password,
So that I can start using UnifyData.AI to search my organization's data.
```

---

**UI/UX Description:**

**Page:** `/signup`

**Layout:**
- Centered form on clean white background
- UnifyData.AI logo at top
- Two-column layout (desktop): Form on left, value props/testimonials on right
- Mobile: Single column, stacked

**Form Fields:**
1. **Email** (text input)
   - Placeholder: "you@company.com"
   - Icon: Envelope
   - Auto-focus on page load

2. **Password** (password input)
   - Placeholder: "Create a strong password"
   - Toggle show/hide button (eye icon)
   - Real-time password strength indicator (weak/medium/strong)
   - Requirements shown below:
     - ✓ At least 12 characters
     - ✓ One uppercase letter
     - ✓ One lowercase letter
     - ✓ One number
     - ✓ One special character (!@#$%^&*)

3. **Confirm Password** (password input)
   - Placeholder: "Confirm your password"
   - Show checkmark icon when matches

4. **Full Name** (text input)
   - Placeholder: "John Doe"

5. **Company Name** (text input)
   - Placeholder: "Acme Corp"
   - Helper text: "This will be your organization name"

6. **Terms Checkbox**
   - Label: "I agree to the [Terms of Service] and [Privacy Policy]"
   - Links open in new tab

**Buttons:**
- **Primary CTA:** "Create Account" (full width, blue, large)
- **Secondary:** "Sign up with Google" (white with Google logo, above form)
- **Tertiary:** "Already have an account? Log in" (text link below)

---

**Acceptance Criteria:**

✅ **Email Validation:**
- Must be valid email format (regex: `^[^\s@]+@[^\s@]+\.[^\s@]+$`)
- Must not already exist in database (case-insensitive)
- Shows error: "Email already registered. [Log in instead?]" (with link)

✅ **Password Requirements:**
- Minimum 12 characters
- At least 1 uppercase letter (A-Z)
- At least 1 lowercase letter (a-z)
- At least 1 number (0-9)
- At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
- Shows real-time validation (green checkmarks as requirements met)
- Password strength indicator updates dynamically:
  - Weak (red): <12 chars or missing requirements
  - Medium (orange): 12+ chars, 3/4 requirements
  - Strong (green): 12+ chars, all requirements + >16 chars

✅ **Password Confirmation:**
- Must match password field exactly
- Shows error below field: "Passwords don't match"
- Shows green checkmark when matches

✅ **Company Name (Organization):**
- Required field
- Minimum 2 characters
- Creates new organization with this name
- Sets `organizations.slug` = lowercase, hyphenated (e.g., "Acme Corp" → "acme-corp")
- If slug conflicts, append number (acme-corp-2)

✅ **User Creation:**
- Creates user record in `users` table
- Sets `user.role = 'admin'` (first user is always admin)
- Sets `user.org_id = new_org.id`
- Hashes password with bcrypt (cost factor 12)
- Sets `user.is_email_verified = false`

✅ **Organization Creation:**
- Creates org record in `organizations` table
- Sets `org.plan = 'trial'` (14-day trial by default)
- Sets `org.max_data_sources = 5` (trial limit)
- Sets `org.max_users = 10` (trial limit)

✅ **Email Verification:**
- Sends verification email to user's email
- Email contains:
  - Welcome message
  - Verification link (token valid for 24 hours)
  - CTA button: "Verify Email"
- Token stored in database (or JWT with short expiry)

✅ **Redirect After Signup:**
- Redirects to `/onboarding` (welcome tour)
- Sets JWT tokens (access + refresh) in response
- Stores refresh token in HTTPOnly cookie

✅ **Error Handling:**
- All validation errors shown inline (below field, red text)
- Form submission shows loading state (button disabled, spinner)
- Network errors: "Something went wrong. Please try again."
- Generic server errors: "Unable to create account. Contact support."

✅ **Analytics:**
- Track event: "user_signup_started" (on page load)
- Track event: "user_signup_completed" (on success)
- Track event: "user_signup_failed" (on error, with error type)

---

**Edge Cases:**

**Case 1: Email Already Exists**
- **Scenario:** User enters email that's already registered
- **Behavior:**
  - Show error below email field: "This email is already registered."
  - Show link: "[Log in instead?]" → redirects to `/login` with email pre-filled
- **API Response:** `400 Bad Request` with error code `EMAIL_EXISTS`

**Case 2: Company Name Already Taken (Slug Conflict)**
- **Scenario:** User enters company name that produces duplicate slug
- **Behavior:**
  - Allow signup (multiple orgs can have same name)
  - Generate unique slug: `acme-corp-2`, `acme-corp-3`, etc.
  - User doesn't see slug (internal only)

**Case 3: Network Error During Signup**
- **Scenario:** API request fails due to network issue
- **Behavior:**
  - Show error toast: "Network error. Please check your connection."
  - Show "Retry" button (preserves form data, doesn't clear)
  - Don't auto-reload page (preserve user's input)

**Case 4: Email Delivery Fails**
- **Scenario:** Verification email fails to send (SMTP error)
- **Behavior:**
  - Signup still succeeds (don't block user)
  - Show message: "Account created! Verification email sent to {email}. If you don't see it, check your spam folder."
  - Provide "Resend verification email" link on `/dashboard` (banner at top)
- **Backend:** Log email failure, retry sending after 5 minutes (background job)

**Case 5: OAuth Flow Cancelled**
- **Scenario:** User clicks "Sign up with Google", then cancels authorization
- **Behavior:**
  - Redirect back to `/signup`
  - Show message: "Sign up cancelled. You can sign up with email or try again."
  - Don't create any user record

**Case 6: OAuth Account Already Linked**
- **Scenario:** User signs up with Google, but that Google account is already linked to another UnifyData account
- **Behavior:**
  - Show error: "This Google account is already linked to an existing account. [Log in instead?]"
  - Provide link to `/login`

**Case 7: Weak Password Submitted**
- **Scenario:** User bypasses client-side validation (e.g., disabled JS) and submits weak password
- **Behavior:**
  - Backend validates password requirements
  - Return `400 Bad Request` with error: "Password does not meet requirements"
  - Show error on frontend

**Case 8: Terms Not Accepted**
- **Scenario:** User submits form without checking terms checkbox
- **Behavior:**
  - Show error below checkbox: "You must agree to the Terms of Service and Privacy Policy"
  - Prevent form submission

**Case 9: Rate Limiting (Abuse Prevention)**
- **Scenario:** Someone tries to create 100 accounts from same IP in 1 minute
- **Behavior:**
  - After 5 signup attempts from same IP in 10 minutes, show: "Too many signup attempts. Please try again in 10 minutes."
  - Return `429 Too Many Requests`

---

**API Endpoint:**

```http
POST /api/auth/register
Content-Type: application/json

Request Body:
{
  "email": "john@acme.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "company_name": "Acme Corp"
}

Success Response (201 Created):
{
  "user": {
    "id": "uuid-1234",
    "email": "john@acme.com",
    "full_name": "John Doe",
    "role": "admin",
    "org_id": "uuid-5678",
    "is_email_verified": false
  },
  "organization": {
    "id": "uuid-5678",
    "name": "Acme Corp",
    "slug": "acme-corp",
    "plan": "trial",
    "trial_ends_at": "2025-01-29T00:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 900
  }
}

Error Response (400 Bad Request):
{
  "error": {
    "code": "EMAIL_EXISTS",
    "message": "This email is already registered",
    "field": "email"
  }
}

Error Response (422 Unprocessable Entity):
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Password does not meet requirements",
    "field": "password",
    "details": {
      "min_length": false,
      "uppercase": true,
      "lowercase": true,
      "number": true,
      "special_char": false
    }
  }
}
```

---

**Database Changes:**

**Create User:**
```sql
INSERT INTO users (
  id, email, password_hash, full_name, role, org_id,
  is_email_verified, created_at, updated_at
) VALUES (
  gen_random_uuid(),
  'john@acme.com',
  '$2b$12$...',  -- bcrypt hash
  'John Doe',
  'admin',
  '{{org_id}}',
  false,
  NOW(),
  NOW()
);
```

**Create Organization:**
```sql
INSERT INTO organizations (
  id, name, slug, plan, status, max_data_sources, max_users,
  trial_ends_at, created_at, updated_at
) VALUES (
  gen_random_uuid(),
  'Acme Corp',
  'acme-corp',
  'trial',
  'active',
  5,
  10,
  NOW() + INTERVAL '14 days',
  NOW(),
  NOW()
);
```

**Create Verification Token:**
```sql
INSERT INTO email_verification_tokens (
  id, user_id, token, expires_at, created_at
) VALUES (
  gen_random_uuid(),
  '{{user_id}}',
  '{{random_token}}',  -- UUID or JWT
  NOW() + INTERVAL '24 hours',
  NOW()
);
```

---

**Frontend Implementation Notes:**

**Tech Stack:**
- Next.js App Router (server actions for form submission)
- React Hook Form (form state management)
- Zod (validation schema)
- TanStack Query (API mutations)

**Key Files:**
- `app/signup/page.tsx` - Main signup page
- `components/auth/SignupForm.tsx` - Form component
- `lib/validation/auth.ts` - Zod schemas
- `lib/api/auth.ts` - API client functions

**Password Strength Indicator:**
- Use library: `zxcvbn` (Dropbox's password strength estimator)
- Shows bar below password field (0-4 scale):
  - 0-1: Weak (red)
  - 2: Medium (orange)
  - 3-4: Strong (green)

**Google OAuth:**
- Use `next-auth` or `@react-oauth/google`
- Redirect to Google OAuth consent screen
- Callback URL: `/api/auth/callback/google`
- Exchange code for tokens server-side

---

### Feature 1.2: User Login

**Priority:** P0 (Must Have)
**Effort:** Small (1-2 days)

**User Story:**
```
As a registered user,
I want to log in with my email and password,
So that I can access my organization's data and search functionality.
```

---

**UI/UX Description:**

**Page:** `/login`

**Layout:**
- Centered form (similar to signup)
- UnifyData.AI logo at top
- Value props on right (desktop)

**Form Fields:**
1. **Email** (text input)
   - Placeholder: "you@company.com"
   - Autofocus on load

2. **Password** (password input)
   - Placeholder: "Enter your password"
   - Toggle show/hide button

3. **Remember Me** (checkbox)
   - Label: "Keep me logged in for 30 days"
   - Default: unchecked

**Links:**
- "Forgot password?" (below password field) → `/forgot-password`
- "Don't have an account? Sign up" (below form) → `/signup`

**Buttons:**
- **Primary CTA:** "Log In" (full width, blue)
- **Secondary:** "Sign in with Google" (white with Google logo)

---

**Acceptance Criteria:**

✅ **Email & Password Validation:**
- Email: Must be valid format (client-side only, server checks database)
- Password: No client-side validation (accept any input)
- Shows error if credentials invalid: "Invalid email or password"
- **Security:** Don't reveal whether email exists (generic error message)

✅ **Authentication:**
- Backend verifies email exists in database
- Backend verifies password hash matches (bcrypt.compare)
- Returns JWT tokens (access + refresh) on success
- Sets refresh token in HTTPOnly cookie

✅ **Token Expiry:**
- Access token: 15 minutes
- Refresh token: 7 days (default) or 30 days (if "Remember me" checked)

✅ **Redirect After Login:**
- Redirects to `/dashboard` on success
- If user accessed protected page before login (e.g., `/search`), redirect to that page after login

✅ **Rate Limiting:**
- Max 5 failed login attempts per email per 15 minutes
- After 5 failures, show: "Too many failed attempts. Try again in 15 minutes."
- Store failed attempts in Redis (key: `login_attempts:{email}`, TTL: 15 min)

✅ **Security Logging:**
- Log all login attempts (success + failure) in `audit_logs` table
- Store: timestamp, user_id (if success), email (if failure), IP address, user agent
- Use for security monitoring and anomaly detection

✅ **"Remember Me" Functionality:**
- If checked: Refresh token expires in 30 days (instead of 7)
- If unchecked: Refresh token expires in 7 days

✅ **Error Messages:**
- Invalid credentials: "Invalid email or password"
- Account not verified: "Please verify your email before logging in. [Resend verification email]"
- Too many attempts: "Too many failed login attempts. Try again in 15 minutes."
- Account suspended: "Your account has been suspended. Contact support@unifydata.ai"

---

**Edge Cases:**

**Case 1: Wrong Password**
- **Behavior:** Show error: "Invalid email or password" (don't specify which is wrong)
- **Security:** Don't reveal if email exists (prevents enumeration)

**Case 2: Account Not Verified**
- **Behavior:**
  - Show error: "Please verify your email before logging in."
  - Show link: "[Resend verification email]"
  - Clicking link sends new verification email

**Case 3: Too Many Failed Attempts**
- **Behavior:**
  - After 5 failed attempts in 15 minutes: Show error + block login
  - Reset counter after 15 minutes (Redis TTL)
  - Option: Show CAPTCHA after 3 attempts (future enhancement)

**Case 4: Password Expired (Future)**
- **Behavior:**
  - If password hasn't been changed in 90 days (enterprise policy)
  - Redirect to "Change password" page
  - User must set new password before accessing dashboard

**Case 5: Account Locked/Suspended**
- **Behavior:**
  - If `user.status = 'suspended'`: Show error + contact support link
  - Don't allow login
  - Admin can unsuspend from admin panel

**Case 6: Session Already Active (Security)**
- **Behavior:**
  - Allow concurrent sessions (don't force logout from other devices)
  - Future: Option to "Log out all devices" in settings

**Case 7: OAuth Email Mismatch**
- **Scenario:** User signs up with email+password, then tries to login with Google using different email
- **Behavior:**
  - If Google email doesn't match any existing user: Create new account (separate org)
  - If Google email matches existing user: Link Google OAuth to that account

---

**API Endpoint:**

```http
POST /api/auth/login
Content-Type: application/json

Request Body:
{
  "email": "john@acme.com",
  "password": "SecurePass123!",
  "remember_me": false
}

Success Response (200 OK):
{
  "user": {
    "id": "uuid-1234",
    "email": "john@acme.com",
    "full_name": "John Doe",
    "role": "admin",
    "org_id": "uuid-5678",
    "org_name": "Acme Corp"
  },
  "tokens": {
    "access_token": "eyJhbGc...",
    "expires_in": 900
  }
}
// Refresh token set in Set-Cookie header (HTTPOnly, Secure, SameSite=Strict)

Error Response (401 Unauthorized):
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}

Error Response (403 Forbidden):
{
  "error": {
    "code": "EMAIL_NOT_VERIFIED",
    "message": "Please verify your email before logging in"
  }
}

Error Response (429 Too Many Requests):
{
  "error": {
    "code": "TOO_MANY_ATTEMPTS",
    "message": "Too many failed login attempts. Try again in 15 minutes.",
    "retry_after": 900  // seconds
  }
}
```

---

**Frontend Implementation Notes:**

**Session Management:**
- Store access token in memory (React state or context)
- Don't store in localStorage (XSS vulnerability)
- Refresh token stored in HTTPOnly cookie (backend sets it)
- On page refresh: Check if refresh token cookie exists
  - If yes: Call `/api/auth/refresh` to get new access token
  - If no: Redirect to `/login`

**Auto-Refresh Access Token:**
- When access token expires (15 min): Automatically call `/api/auth/refresh`
- Use interceptor in API client (axios/fetch)
- If refresh fails (401): Clear session, redirect to `/login`

---

### Feature 1.3: Password Reset

**Priority:** P1 (Should Have)
**Effort:** Small (1-2 days)

**User Story:**
```
As a user who forgot my password,
I want to reset it via email,
So that I can regain access to my account.
```

---

**Flow:**

**Step 1: Request Reset Link**
- User clicks "Forgot password?" on `/login`
- Redirects to `/forgot-password`
- Enter email → Submit
- Show message: "If an account exists with that email, a reset link has been sent."

**Step 2: Receive Email**
- User receives email with reset link
- Link format: `https://app.unifydata.ai/reset-password?token={token}`
- Token valid for 1 hour

**Step 3: Reset Password**
- User clicks link → Redirects to `/reset-password?token={token}`
- Form shows:
  - New password field
  - Confirm new password field
  - "Reset Password" button
- Submit → Password updated
- Redirect to `/login` with success message

---

**UI/UX Description:**

**Page 1: `/forgot-password`**
- Heading: "Reset your password"
- Subheading: "Enter your email and we'll send you a reset link."
- Email input field
- "Send Reset Link" button
- "Back to login" link

**Page 2: `/reset-password?token={token}`**
- Heading: "Create new password"
- New password field (with strength indicator)
- Confirm password field
- "Reset Password" button
- Password requirements shown (same as signup)

---

**Acceptance Criteria:**

✅ **Request Reset Link:**
- User enters email
- Backend checks if email exists
- If exists: Generate reset token, send email
- If not exists: Still show success message (security - don't reveal accounts)
- Message: "If an account exists with that email, a reset link has been sent. Check your inbox."

✅ **Reset Token:**
- Token is UUID stored in database (or JWT with short expiry)
- Token valid for 1 hour only
- Token is single-use (invalidated after password reset)
- Store in `password_reset_tokens` table:
  - `id`, `user_id`, `token`, `expires_at`, `used_at`, `created_at`

✅ **Email Content:**
- Subject: "Reset your UnifyData.AI password"
- Body:
  - "You requested a password reset for your UnifyData.AI account."
  - "Click the button below to reset your password:"
  - CTA button: "Reset Password" → links to reset page
  - "This link expires in 1 hour."
  - "If you didn't request this, you can safely ignore this email."

✅ **Reset Password Page:**
- Validates token on page load
  - If expired: Show error "This reset link has expired. [Request new link]"
  - If invalid: Show error "Invalid reset link. [Request new link]"
  - If already used: Show error "This link has already been used. [Request new link]"
- New password must meet same requirements as signup
- Shows password strength indicator
- Confirm password must match

✅ **Password Update:**
- Hashes new password with bcrypt
- Updates `users.password_hash`
- Marks token as used (`used_at = NOW()`)
- Logs password change in audit log
- Invalidates all existing sessions (optional: force re-login on all devices)

✅ **Confirmation:**
- Shows success message: "Your password has been reset successfully."
- Redirects to `/login` after 3 seconds
- Sends confirmation email: "Your UnifyData.AI password was changed"

---

**Edge Cases:**

**Case 1: Token Expired**
- **Behavior:** Show error: "This reset link has expired. [Request a new one]"
- **Link:** Takes user back to `/forgot-password`

**Case 2: Token Already Used**
- **Behavior:** Show error: "This link has already been used. If you need to reset your password again, [request a new link]"

**Case 3: Token Invalid (Tampered)**
- **Behavior:** Show error: "This reset link is invalid. Please [request a new one]"

**Case 4: Email Delivery Fails**
- **Behavior:**
  - User doesn't receive email
  - Still show success message (don't reveal failure)
  - Backend logs error, retries after 5 minutes

**Case 5: User Changes Password Multiple Times**
- **Behavior:**
  - Each request generates new token
  - Old tokens remain valid until expired (1 hour)
  - Rate limit: Max 3 reset requests per email per hour

**Case 6: Weak Password Submitted**
- **Behavior:** Show validation error (same as signup)

---

**API Endpoints:**

```http
POST /api/auth/forgot-password
Content-Type: application/json

Request Body:
{
  "email": "john@acme.com"
}

Success Response (200 OK):
{
  "message": "If an account exists with that email, a reset link has been sent"
}
// Always returns 200, even if email doesn't exist (security)
```

```http
POST /api/auth/reset-password
Content-Type: application/json

Request Body:
{
  "token": "uuid-or-jwt",
  "new_password": "NewSecurePass456!"
}

Success Response (200 OK):
{
  "message": "Password reset successfully"
}

Error Response (400 Bad Request):
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "This reset link has expired"
  }
}

Error Response (400 Bad Request):
{
  "error": {
    "code": "TOKEN_INVALID",
    "message": "Invalid reset link"
  }
}

Error Response (422 Unprocessable Entity):
{
  "error": {
    "code": "WEAK_PASSWORD",
    "message": "Password does not meet requirements"
  }
}
```

---

## 2. ONBOARDING FLOW (NEW USER)

### Feature 2.1: Welcome & Product Tour

**Priority:** P1 (Should Have)
**Effort:** Medium (2-3 days)

**User Story:**
```
As a new user who just signed up,
I want to see a quick product tour,
So that I understand what UnifyData.AI does and how to use it.
```

---

**UI/UX Description:**

**Trigger:** Shows automatically after user signs up and verifies email (or on first login)

**Format:** Modal overlay (semi-transparent backdrop, centered modal)

**Tour Steps (5 slides):**

**Slide 1: Welcome**
- Heading: "Welcome to UnifyData.AI! 👋"
- Subheading: "Let's take a quick tour to get you started."
- Content:
  - "UnifyData.AI connects all your data sources (Salesforce, Slack, Google Drive, etc.) and lets you search everything in one place using natural language."
  - Illustration: Diagram showing multiple data sources → UnifyData → search bar
- Buttons:
  - "Next" (primary)
  - "Skip Tour" (text link, bottom)

**Slide 2: Connect Data Sources**
- Heading: "Step 1: Connect Your Data Sources"
- Content:
  - "Connect your tools (Salesforce, Slack, Notion, Google Drive, Gmail) in just a few clicks."
  - "We'll securely sync your data and make it searchable."
- Illustration: Screenshot or mockup of data source connection page
- Buttons: "Next", "Previous", "Skip Tour"

**Slide 3: Search in Natural Language**
- Heading: "Step 2: Ask Questions in Plain English"
- Content:
  - "No need for complex queries. Just type your question like you're talking to a colleague."
  - Example queries shown:
    - "What did we discuss about Acme Corp in Slack last week?"
    - "Show me all open deals in Salesforce over €50K"
    - "Find the Q4 sales report"
- Illustration: Animated search bar with example queries
- Buttons: "Next", "Previous", "Skip Tour"

**Slide 4: Get Instant Answers**
- Heading: "Step 3: Get Answers in Seconds"
- Content:
  - "UnifyData.AI searches across all your connected sources and gives you instant answers with links to the original documents."
  - "No more hunting through multiple apps!"
- Illustration: Screenshot of search results with sources
- Buttons: "Next", "Previous", "Skip Tour"

**Slide 5: Ready to Start**
- Heading: "You're All Set! 🚀"
- Content:
  - "Let's connect your first data source and start searching."
- Buttons:
  - "Connect My First Source" (primary, large)
  - "I'll Explore On My Own" (secondary)

---

**Acceptance Criteria:**

✅ **Show Tour on First Login Only:**
- Check `user.onboarding_completed` flag in database
- If `false`: Show tour
- If `true`: Skip tour, go directly to dashboard

✅ **Navigation:**
- Users can navigate forward/backward through slides
- "Next" button on slides 1-4
- "Previous" button on slides 2-5
- "Skip Tour" link on all slides (bottom, gray text)

✅ **Progress Indicator:**
- Show dots or step numbers at bottom: ● ● ○ ○ ○ (slide 1 of 5)
- Current slide highlighted

✅ **Responsive:**
- Works on mobile (modal adapts to screen size)
- Illustrations scale down on small screens
- Text remains readable

✅ **Tour State Saved:**
- If user refreshes page mid-tour, resume at same slide
- Store current slide in localStorage: `onboarding_slide_index`
- Clear localStorage after tour completed

✅ **Skip Tour:**
- Clicking "Skip Tour" or "I'll Explore On My Own" closes modal
- Sets `user.onboarding_completed = true`
- Redirects to `/dashboard`

✅ **Complete Tour:**
- Clicking "Connect My First Source" on slide 5:
  - Sets `user.onboarding_completed = true`
  - Redirects to `/dashboard/data-sources` (connection page)

✅ **Animation:**
- Modal fades in (0.3s)
- Slide transitions smooth (slide or fade, 0.2s)

---

**Edge Cases:**

**Case 1: User Closes Browser Mid-Tour**
- **Behavior:** Tour state saved in localStorage
- **On return:** Resume at same slide (don't start over)

**Case 2: User Skips Tour, Then Wants to See It Again**
- **Behavior:** Add "View Product Tour" link in Help menu
- **Clicking:** Re-shows tour from slide 1

**Case 3: Mobile User**
- **Behavior:** Tour adapts to mobile (smaller text, single-column layout)
- **Illustrations:** Simplified or hidden on small screens

---

**Frontend Implementation:**

**Tech:**
- Component: `<OnboardingTour>` (modal)
- State management: React useState for current slide
- Persist state: localStorage

**Key Functionality:**
```typescript
const [currentSlide, setCurrentSlide] = useState(0);
const totalSlides = 5;

const handleNext = () => {
  if (currentSlide < totalSlides - 1) {
    setCurrentSlide(currentSlide + 1);
    localStorage.setItem('onboarding_slide', currentSlide + 1);
  }
};

const handleSkip = () => {
  markOnboardingComplete();
  router.push('/dashboard');
};
```

---

### Feature 2.2: Connect First Data Source

**Priority:** P0 (Must Have)
**Effort:** Small (included in data source connection feature)

**User Story:**
```
As a new user who completed the product tour,
I want to connect my first data source,
So that I can start searching my organization's data.
```

---

**UI/UX Description:**

**Page:** `/dashboard/data-sources` (or `/onboarding/connect-source`)

**Layout:**
- Heading: "Connect Your First Data Source"
- Subheading: "Choose a data source to get started. You can add more later."
- Grid of 5 connector cards (2 rows, responsive)

**Each Card Shows:**
- Large logo/icon
- Name (e.g., "Salesforce")
- Short description (e.g., "Connect your CRM data")
- "Connect" button (primary, blue)
- Badge (if popular): "Most Popular" (Salesforce, Slack)

**Available Connectors:**
1. **Salesforce** - "Connect your CRM data (accounts, contacts, deals)"
2. **Slack** - "Search conversations and files"
3. **Google Drive** - "Search your documents and files"
4. **Notion** - "Search your workspace pages and databases"
5. **Gmail** - "Search your emails (metadata by default)"

**Footer:**
- "I'll do this later" link (skips onboarding, goes to dashboard)

---

**Acceptance Criteria:**

✅ **Display Connectors:**
- Show all 5 available connectors
- Cards are clickable (entire card acts as button)
- Hover state: Card lifts (shadow) and button changes color

✅ **Connect Button:**
- Clicking "Connect" triggers OAuth flow (see Feature 3.2-3.6 for details)
- Opens OAuth popup or redirects to OAuth page
- After successful connection:
  - Close popup/redirect back
  - Show success message: "Salesforce connected! Syncing your data..."
  - Show sync progress (spinner + text)
  - Update card to show "Connected" badge

✅ **Skip Option:**
- "I'll do this later" link at bottom
- Clicking: Marks onboarding as complete, redirects to `/dashboard`
- User can connect sources later from dashboard

✅ **Onboarding Progress:**
- If using multi-step onboarding:
  - Show progress: "Step 1 of 2: Connect Data Source"
  - After connection, move to "Step 2: Try Your First Search"

✅ **Multiple Connections:**
- After connecting first source, show prompt:
  - "Great! Want to connect another source?"
  - Show same grid (already-connected sources show "Connected" badge)
  - User can connect multiple sources or proceed

---

**Edge Cases:**

**Case 1: User Skips Connection**
- **Behavior:** Can still access dashboard
- **Banner on Dashboard:** "Connect your first data source to start searching" (with CTA button)

**Case 2: Connection Fails**
- **Behavior:** Show error message (see Feature 3.2-3.6 for error handling)
- **Allow retry:** "Try Again" button

**Case 3: User Already Has Connections (Returning)**
- **Behavior:** Don't show onboarding
- **Show dashboard directly**

---

### Feature 2.3: First Search Tutorial

**Priority:** P2 (Nice to Have)
**Effort:** Small (1 day)

**User Story:**
```
As a new user who just connected a data source,
I want to try my first search,
So that I understand how the search feature works.
```

---

**UI/UX Description:**

**Trigger:** After first data source connected and sync starts

**Page:** `/dashboard/search` or modal overlay on dashboard

**Layout:**
- Heading: "Try Your First Search!"
- Subheading: "Ask a question in plain English. Here are some examples:"

**Pre-populated Examples (Clickable Pills):**
- "Show me all open deals in Salesforce"
- "What did we discuss about [Customer Name] in Slack?"
- "Find the Q4 report in Google Drive"
- "Who created the [Project Name] doc in Notion?"

**Search Bar:**
- Large, centered search input
- Placeholder: "Ask a question about your data..."
- Examples rotate in placeholder (type animation)

**Illustration/Demo:**
- If real data not synced yet: Show demo results
- If data synced: Show actual results

---

**Acceptance Criteria:**

✅ **Show After First Connection:**
- Appears after first data source connected
- Can be modal or full page
- Skippable (close button or "Skip" link)

✅ **Pre-populated Queries:**
- Clickable examples shown as pills
- Clicking fills search bar with query
- User can edit before submitting

✅ **Demo Mode (If Data Not Ready):**
- If sync still in progress: Show "Data syncing... Meanwhile, try these demo results"
- Show sample results (not real data)
- Clear label: "Demo Results" badge

✅ **Real Search:**
- If data synced: Execute real search
- Show actual results from user's data

✅ **Completion:**
- After first successful search: Mark onboarding complete
- Show tooltip: "Great! You can search anytime from the search bar at the top."
- Don't show this tutorial again

---

**Edge Cases:**

**Case 1: Data Still Syncing**
- **Behavior:** Show demo results with message: "Your data is syncing. Check back in a few minutes for real results."

**Case 2: No Results Found**
- **Behavior:** Show message: "No results found. Try another question or wait for sync to complete."

**Case 3: User Skips**
- **Behavior:** Mark onboarding complete, don't show again

---

## 3. DATA SOURCE CONNECTION (CORE FEATURE)

### Feature 3.1: Data Sources Dashboard

**Priority:** P0 (Must Have)
**Effort:** Medium (3-4 days)

**User Story:**
```
As a user,
I want to see all my connected data sources in one place,
So that I can manage connections, view sync status, and add new sources.
```

---

**UI/UX Description:**

**Page:** `/dashboard/data-sources`

**Layout:**

**Header:**
- Heading: "Data Sources"
- Subheading: "Connect and manage your data sources"
- "+ Connect New Source" button (top right, primary blue)

**Grid Layout:**
- Responsive grid:
  - Desktop: 3-4 columns
  - Tablet: 2 columns
  - Mobile: 1 column
- Cards for connected sources appear first
- Available (not connected) sources appear below

---

**Connected Source Card:**

**Card Components:**
1. **Logo & Name** (top left)
   - Large icon (64×64px)
   - Name below (e.g., "Salesforce")

2. **Status Badge** (top right)
   - "Active" (green)
   - "Syncing" (blue, with spinner)
   - "Error" (red)
   - "Paused" (gray)

3. **Sync Info** (middle)
   - "Last synced: 5 minutes ago"
   - "Documents indexed: 1,234"
   - Progress bar (if syncing): "Syncing... 40% (2,000 of 5,000 records)"

4. **Actions** (bottom)
   - "Sync Now" button (icon: refresh)
   - "Settings" button (icon: gear)
   - "Disconnect" button (icon: trash, red text)

**Hover State:**
- Card lifts (shadow)
- Actions become more visible

---

**Available Source Card:**

**Card Components:**
1. **Logo & Name**
2. **Description** (e.g., "Connect your CRM data")
3. **"Connect" button** (primary blue)

**Hover State:**
- Card lifts
- "Connect" button darker blue

---

**Acceptance Criteria:**

✅ **Display All Sources:**
- Shows 5 available connectors (Salesforce, Slack, Google Drive, Notion, Gmail)
- Connected sources show at top
- Available sources show below (or in separate tab)

✅ **Status Badges:**
- **Active:** Green, data source connected and syncing successfully
- **Syncing:** Blue with spinner, sync in progress
- **Error:** Red, last sync failed (show error message on hover or click)
- **Paused:** Gray, user manually paused syncing

✅ **Real-time Updates:**
- Sync status updates automatically (WebSocket or polling every 5 seconds)
- Progress bar animates during sync
- "Last synced" timestamp updates after sync completes

✅ **Sync Now Button:**
- Triggers manual sync immediately
- Disables button if already syncing ("Syncing..." with spinner)
- Shows success toast: "Sync started for Salesforce"

✅ **Settings Button:**
- Opens settings modal or navigates to `/dashboard/data-sources/[id]/settings`
- Shows connector-specific configuration (see Feature 3.2-3.6)

✅ **Disconnect Button:**
- Shows confirmation modal: "Are you sure you want to disconnect Salesforce? All indexed data will be removed."
- Two buttons: "Cancel" (secondary), "Disconnect" (danger, red)
- After disconnect:
  - Deletes data source record
  - Triggers background job to remove indexed data (vectors, graph nodes)
  - Shows success toast: "Salesforce disconnected"

✅ **Search/Filter (Future):**
- Search bar at top (if many sources connected)
- Filter by status: All, Active, Error

✅ **Empty State:**
- If no sources connected: Show large illustration + CTA
  - "No data sources connected yet"
  - "Connect your first source to start searching"
  - "Connect Source" button

---

**Edge Cases:**

**Case 1: Sync Fails**
- **Behavior:** Status badge shows "Error"
- **Hover:** Shows error message tooltip: "Token expired. Please reconnect."
- **Clicking card:** Opens error details modal with "Reconnect" button

**Case 2: Very Long Sync**
- **Behavior:** Show progress bar + estimated time remaining
- **Example:** "Syncing... 20% complete. ~15 minutes remaining."

**Case 3: Multiple Sources Syncing**
- **Behavior:** All show "Syncing" status simultaneously
- **Performance:** Ensure UI doesn't lag (throttle updates)

**Case 4: User Disconnects While Syncing**
- **Behavior:** Show warning: "Sync in progress. Disconnecting will cancel the sync. Continue?"

---

**API Endpoints:**

```http
GET /api/data-sources
Response:
{
  "sources": [
    {
      "id": "uuid-1",
      "type": "salesforce",
      "name": "Salesforce",
      "status": "active",
      "last_sync_at": "2025-01-15T10:30:00Z",
      "documents_indexed": 1234,
      "sync_progress": null
    },
    {
      "id": "uuid-2",
      "type": "slack",
      "name": "Slack",
      "status": "syncing",
      "last_sync_at": "2025-01-15T10:25:00Z",
      "documents_indexed": 5678,
      "sync_progress": {
        "current": 2000,
        "total": 5000,
        "percentage": 40
      }
    }
  ],
  "available": ["salesforce", "slack", "google_drive", "notion", "gmail"]
}
```

```http
POST /api/data-sources/{id}/sync
Response:
{
  "job_id": "uuid-job-123",
  "message": "Sync started"
}
```

```http
DELETE /api/data-sources/{id}
Response:
{
  "message": "Data source disconnected successfully"
}
```

---

(Continuing with Features 3.2-3.6 and 4.1-4.3 follows same detailed structure...)

---

## 4. DATA SYNC MANAGEMENT

### Feature 4.1: Manual Sync Trigger

**Priority:** P0 (Must Have)
**Effort:** Small (included in Feature 3.1)

**User Story:**
```
As a user,
I want to manually trigger a sync for a data source,
So that I can get the latest data immediately without waiting for the scheduled sync.
```

---

**UI/UX Description:**

**Location:** Data source card on `/dashboard/data-sources`

**Button:** "Sync Now" (with refresh icon)

**States:**
- **Default:** Blue button, enabled
- **Syncing:** Gray button, disabled, spinner icon, text: "Syncing..."
- **Success:** Green checkmark briefly (2 seconds), then back to default

---

**Acceptance Criteria:**

✅ **Trigger Sync:**
- Clicking "Sync Now" triggers background job
- API call: `POST /api/data-sources/{id}/sync`
- Returns job ID immediately (doesn't wait for sync to finish)

✅ **Button States:**
- Disabled if already syncing: "Syncing..." (gray, spinner)
- Prevents duplicate syncs: If clicked while syncing, show toast: "Sync already in progress"

✅ **Real-time Progress:**
- Button text updates: "Syncing... 40%"
- Or separate progress bar below button

✅ **Success Feedback:**
- After sync completes: Show toast: "Sync complete! X new documents added."
- Button shows checkmark briefly, then resets

✅ **Error Handling:**
- If sync fails: Show error toast: "Sync failed. [View Details]"
- Button resets to "Sync Now"
- Error details available in sync history

✅ **Rate Limiting:**
- Prevent spam: Max 1 manual sync per 5 minutes per source
- If too soon: Show toast: "Please wait X minutes before syncing again"

---

**Edge Cases:**

**Case 1: Sync Already in Progress**
- **Behavior:** Button disabled, show "Syncing..." (don't allow second sync)

**Case 2: Sync Fails Immediately**
- **Behavior:** Show error toast with retry button

**Case 3: User Refreshes Page During Sync**
- **Behavior:** On page load, check sync status
- **If syncing:** Show "Syncing..." button state

---

### Feature 4.2: Sync History & Logs

**Priority:** P2 (Nice to Have)
**Effort:** Medium (2-3 days)

**User Story:**
```
As a user,
I want to see the sync history for each data source,
So that I can troubleshoot issues and understand when data was last updated.
```

---

**UI/UX Description:**

**Location:** Accessible from data source settings

**Page:** `/dashboard/data-sources/[id]/history`

**Layout:**

**Header:**
- Heading: "Sync History - Salesforce"
- Filters:
  - Status dropdown: All, Success, Failed, Partial
  - Date range picker: Last 7 days, Last 30 days, Custom
- "Export to CSV" button (secondary)

**Table:**

| Timestamp | Status | Documents | Duration | Actions |
|-----------|--------|-----------|----------|---------|
| Jan 15, 10:30 AM | ✅ Success | 1,234 added, 56 updated | 2m 34s | View Details |
| Jan 15, 10:00 AM | ❌ Failed | 0 | 15s | Retry |
| Jan 15, 9:30 AM | ⚠️ Partial | 800 added, 200 failed | 5m 12s | View Details |

---

**Acceptance Criteria:**

✅ **Display History:**
- Shows last 100 sync jobs by default
- Pagination for older jobs (50 per page)
- Sorted by timestamp (newest first)

✅ **Filters:**
- Filter by status: All, Success, Failed, Partial
- Filter by date range
- Filters update table without page reload

✅ **Status Icons:**
- Success: Green checkmark
- Failed: Red X
- Partial: Yellow warning triangle

✅ **View Details:**
- Clicking "View Details" opens modal or expands row
- Shows:
  - Job ID
  - Start/end time
  - Documents processed breakdown (added, updated, deleted, failed)
  - Error messages (if failed)
  - Sync configuration used

✅ **Retry Button:**
- Only shown for failed syncs
- Clicking triggers new sync with same configuration

✅ **Export:**
- "Export to CSV" downloads CSV file
- Columns: Timestamp, Status, Documents Added, Documents Updated, Documents Failed, Duration, Error Message

---

**Edge Cases:**

**Case 1: No Sync History**
- **Behavior:** Show empty state: "No sync history yet. [Sync Now]"

**Case 2: Very Large History (1000+ jobs)**
- **Behavior:** Pagination (50 per page)
- **Search:** Add search bar to find specific job by ID or date

**Case 3: Detailed Error Logs (Technical)**
- **Behavior:** "View Technical Logs" button for admins
- **Shows:** Full stack trace, API responses (for debugging)

---

### Feature 4.3: Sync Error Handling & Notifications

**Priority:** P1 (Should Have)
**Effort:** Medium (2-3 days)

**User Story:**
```
As a user,
I want to be notified when a sync fails,
So that I can fix the issue and ensure my data stays up-to-date.
```

---

**Notification Strategy:**

**1. In-App Notification (Always):**
- Red badge on data source card: "Error" status
- Notification bell icon (top nav) shows: "Salesforce sync failed"
- Clicking: Opens error details

**2. Email Notification (After 3 Consecutive Failures):**
- Subject: "Action Required: Salesforce sync failing"
- Body:
  - "Your Salesforce data source has failed to sync 3 times."
  - Error message: "Token expired"
  - Action: "Reconnect Salesforce" (button → links to reconnect flow)

**3. Slack Notification (Future, Optional):**
- Post to #unifydata-alerts channel (if Slack integration enabled)

---

**Common Error Messages:**

**Error 1: Token Expired**
- **Message:** "Your Salesforce token has expired. Please reconnect."
- **Action:** "Reconnect" button → triggers OAuth flow
- **User-friendly:** "Your connection expired. Click to reconnect."

**Error 2: API Rate Limit**
- **Message:** "Salesforce API rate limit reached. Sync will resume automatically."
- **Action:** None (auto-retry with backoff)
- **User-friendly:** "Syncing slower than usual due to API limits. This is normal."

**Error 3: Permission Denied**
- **Message:** "Insufficient permissions to access X object in Salesforce."
- **Action:** "Grant Permissions" button → re-runs OAuth with additional scopes
- **User-friendly:** "We need additional permissions to sync X. Please grant access."

**Error 4: Network Error**
- **Message:** "Network error. Retrying automatically..."
- **Action:** Auto-retry (3 attempts with exponential backoff)
- **User-friendly:** "Temporary network issue. We're retrying."

---

**Acceptance Criteria:**

✅ **In-App Notifications:**
- Badge on data source card shows error status
- Notification bell shows unread count
- Clicking notification: Opens error details + suggested action

✅ **Email Notifications:**
- Sent after 3 consecutive sync failures
- Email includes:
  - Data source name
  - Error message (user-friendly)
  - Action button (reconnect, grant permissions, etc.)
  - Link to sync history for more details

✅ **Error Messages:**
- Clear, actionable, non-technical
- Provide "Fix" button when possible
- Link to documentation for complex issues

✅ **Auto-Retry Logic:**
- Network errors: Retry 3× with exponential backoff (1s, 2s, 4s)
- Rate limits: Slow down sync, retry after cooldown period
- Token expiry: Don't retry (requires user action)

✅ **Alert Admins Only:**
- Only org admins receive email notifications (not all users)
- Users see in-app notifications

✅ **Mute Notifications (Future):**
- Option to mute notifications for specific source (if user knows issue, working on fix)

---

**Edge Cases:**

**Case 1: Transient Error (Network Glitch)**
- **Behavior:** Auto-retry succeeds, no notification sent
- **Log:** Error logged but not surfaced to user

**Case 2: Permanent Error (Invalid Credentials)**
- **Behavior:** Fail immediately, notify user, don't retry

**Case 3: Partial Sync Success**
- **Behavior:** Mark sync as "partial success"
- **Notification:** "Some documents failed to sync. [View Details]"

---

**API Endpoint:**

```http
GET /api/notifications
Response:
{
  "notifications": [
    {
      "id": "uuid-1",
      "type": "sync_error",
      "source_id": "uuid-sf-1",
      "source_name": "Salesforce",
      "message": "Sync failed: Token expired",
      "action": "reconnect",
      "timestamp": "2025-01-15T10:30:00Z",
      "read": false
    }
  ],
  "unread_count": 3
}
```

---

**END OF PART 1**

---

## Next Steps

**MVP Feature Specifications - Part 2** will cover:
- **Feature 5:** Search Interface (natural language query, results display, filters)
- **Feature 6:** Knowledge Graph Visualization (basic graph view, entity explorer)
- **Feature 7:** User Settings (profile, preferences, password change)
- **Feature 8:** Organization Management (invite users, manage roles, billing)

Ready to implement these features! 🚀
