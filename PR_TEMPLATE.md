## 📌 Description
Adds user preference system allowing users to customize advice language and tone. Includes admin tools for managing preferences and fixes database model issues plus Windows console encoding errors.

Fixes: N/A

---

## 🔧 Type of Change
Please mark the relevant option(s):

- [ ] 🐛 Bug fix
- [x] ✨ New feature
- [ ] 📝 Documentation update
- [ ] ♻️ Refactor / Code cleanup
- [ ] 🎨 UI / Styling change
- [ ] 🚀 Other (please describe):

---

## 🧪 How Has This Been Tested?
Describe the tests you ran to verify your changes.

- [x] Manual testing
- [ ] Automated tests
- [ ] Not tested (please explain why)

**Testing performed:**
- Verified user preference creation and updates via admin CLI
- Tested preference management in admin GUI
- Confirmed encoding fix resolves charmap errors on Windows
- Validated model migrations apply successfully

---

## 📸 Screenshots (if applicable)
Add screenshots or screen recordings to show UI changes.

---

## ✅ Checklist
Please confirm the following:

- [x] My code follows the project's coding style
- [x] I have tested my changes
- [ ] I have updated documentation where necessary
- [x] This PR does not introduce breaking changes

---

## 📝 Additional Notes

**Commits included:**
- `32d5e73` - fix: Replace Unicode emoji prints with logger to fix charmap encoding error
- `369d39b` - fix: Add missing columns to Question and User models
- `69a8c45` - feat: Add user preferences for advice language and tone
- `9f17863` - feat: Add user preference management to admin CLI and GUI

**Database changes:** New user preferences table added via migration.
