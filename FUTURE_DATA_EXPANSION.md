# Future Data Expansion Ideas

**Current:** ~2 MB/year (just metadata)
**Modern drives:** 500GB-1TB available → we're using 0.0004% of storage

---

## 💡 High-Value Additions (Priority Order)

### 1. **Screenshots** ⭐ HIGHEST VALUE
- **Storage:** ~100 GB/year (JPEG quality 70)
- **Why:** Visual proof, re-analyze later, find exact errors, billing proof
- **Privacy:** Auto-blur after 30 days, encrypt, sensitive-app detection
- **Use cases:** Freelancer billing, error recall, visual work journal

### 2. **OCR Text (Full-Text Search)**
- **Storage:** ~3 GB/year
- **Why:** Search everything you've ever seen on screen
- **Implementation:** Tesseract OCR or Gemini Vision
- **Query:** "find 'authentication error'" across all screenshots

### 3. **Granular Focus Timeline**
- **Storage:** ~15 MB/year
- **Why:** Track every window switch, true context-switch metrics
- **Value:** Exact focus time, identify distractions immediately

### 4. **Browser History Integration**
- **Storage:** ~100 MB/year
- **Why:** Complete web activity, link research to code
- **Query:** "What article did I read about async Python?"

### 5. **File System Activity**
- **Storage:** ~30 MB/year
- **Why:** Track files opened/edited, project time allocation
- **Query:** "When did I last touch that config file?"

### 6. **Clipboard History**
- **Storage:** ~50 MB/year
- **Why:** Recall code snippets, commands, links
- **Query:** "What was that command I copied yesterday?"

---

## 📊 Storage Breakdown

| Feature | Storage/Year | Implementation Time |
|---------|--------------|---------------------|
| Current (metadata) | 2 MB | ✅ Done |
| + Screenshots | +100 GB | 4-6 hours |
| + OCR search | +3 GB | 2-3 hours |
| + Granular focus | +15 MB | 2-3 hours |
| + Browser history | +100 MB | 3-4 hours |
| + File activity | +30 MB | 2-3 hours |
| + Clipboard | +50 MB | 1-2 hours |
| **TOTAL** | **~103 GB** | **15-23 hours** |

**With 500GB drive:** 4+ years of complete visual history

---

## 🎯 Killer Use Cases (If Screenshots Saved)

1. **Freelancer billing proof** - Visual timeline of work
2. **Error message recall** - Search screenshots for errors seen weeks ago
3. **Learning journal** - Review tutorials and code you followed
4. **Content creation** - Generate time-lapse videos of coding
5. **Legal/compliance** - Audit trail for sensitive projects
6. **AI re-analysis** - Use future better models on old screenshots

---

## 🔒 Privacy Features Needed

- Blur screenshots after X days (default 30)
- Sensitive app detection (banking, passwords)
- Encryption at rest (optional)
- On-demand delete ("delete last 5 minutes")
- Emergency wipe command

---

## 💭 Key Insight

**Storage is cheap. Your time and memory are precious.**

100 GB/year = $2-3 of hard drive space
Finding that error you saw 3 weeks ago = priceless

---

## 🚀 Recommended Approach

1. **Phase 1:** Add screenshot saving (4-6 hours)
2. **Use for 1 month** - validate the value
3. **Phase 2:** Add OCR + search (2-3 hours)
4. **Phase 3:** Add browser/files/clipboard as needed

---

## 📋 Config Sketch (If Implemented)

```yaml
storage:
  save_screenshots: true
  screenshot_retention_days: 365
  screenshot_compression_quality: 70

privacy:
  blur_after_days: 30
  encrypt_screenshots: false
  sensitive_apps: ["1Password", "Bank", "Bitwarden"]

ocr:
  enabled: true
  engine: "tesseract"  # or "gemini"
```

---

**See:** `CURRENT_STATUS.md` for current priorities
**Decision:** Think about it, then choose if/when to implement
