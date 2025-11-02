# UI Components Visual Guide

## Media Registration Form - Interactive Components Reference

---

## 1. QR Code Generator

```
┌─────────────────────────┐
│   QR Code Preview       │
│                         │
│   ┌─────────────────┐   │
│   │  █▀▀▀▀▀▀▀▀▀█   │   │
│   │  █ ▄▄▄▄▄ █    │   │
│   │  █ █   █ █    │   │  ← Auto-generated from Media ID
│   │  █ █▄▄▄█ █    │   │
│   │  █▄▄▄▄▄▄▄▄█   │   │
│   └─────────────────┘   │
│                         │
│  [Download] [Print]     │  ← Action buttons (appear when QR exists)
└─────────────────────────┘
```

**Trigger:** Input in Media ID field
**Library:** QRCode.js (CDN)
**Size:** 180×180px
**Features:**
- Instant generation
- PNG download
- Print-ready format

---

## 2. Capacity Calculator

```
┌─────────────────────────────────────────────┐
│ Capacity                                    │
│                                             │
│ ┌──────────────┐  ┌────┐                   │
│ │ 2000         │  │ GB │ TB dropdown       │
│ └──────────────┘  └────┘                   │
│                                             │
│ ●━━━━━━━━━━━━━━━━━○─────────────           │  ← Slider
│                                             │
│ ┌─────────────────────────────────────┐    │
│ │███████████░░░░░░░░░░░░░░░░░░░░░░░░│    │  ← Visual bar
│ └─────────────────────────────────────┘    │
│ 0 GB          10 TB            20 TB       │
└─────────────────────────────────────────────┘
```

**Color Coding:**
- 🟢 Green (0-70%): Optimal
- 🟡 Yellow (70-90%): Warning
- 🔴 Red (90-100%): Critical

**Sync Behavior:**
- Input field ↔️ Slider ↔️ Unit selector
- All three update in real-time

---

## 3. Location Picker

```
┌─────────────────────────────────────────────┐
│ Location                                    │
│                                             │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│ │本社ビル   │→ │1F        │→ │R1        │   │  ← Cascading dropdowns
│ └──────────┘  └──────────┘  └──────────┘   │
│                                             │
│ ┌─────────────────────────────────────┐    │
│ │ 本社ビル-1F-R1                       │    │  ← Auto-populated
│ └─────────────────────────────────────┘    │
│                                             │
│ Visual Rack Map:                            │
│ ┌───┬───┬───┬───┐                          │
│ │ R1│ R2│ R3│ R4│                          │
│ │ ✓ │ ✗ │ ✓ │ ✗ │                          │
│ └───┴───┴───┴───┘                          │
│ ✓ = Available (Green)                      │
│ ✗ = Occupied (Red)                         │
└─────────────────────────────────────────────┘
```

**Interaction:**
- Click dropdown OR click rack slot directly
- Visual feedback on hover
- Occupied racks are disabled

---

## 4. Media Type Wizard

### Initial State
```
┌─────────────────────────────────────────────┐
│ Media Type: [Select Type ▼]                │
│                                             │
│ (No type-specific fields shown)             │
└─────────────────────────────────────────────┘
```

### When "Tape" Selected
```
┌─────────────────────────────────────────────┐
│ Media Type: [Tape (LTO) ▼]                 │
│                                             │
│ ┌── Tape-Specific Settings ──────────────┐ │
│ │ 📼 Tape Type                            │ │
│ │   ┌──────────────────────────────┐      │ │
│ │   │ LTO (Linear Tape-Open) ▼     │      │ │
│ │   └──────────────────────────────┘      │ │
│ │                                          │ │
│ │ 📊 LTO Generation                        │ │
│ │   ┌──────────────────────────────┐      │ │
│ │   │ LTO-8 (12TB/30TB) ▼          │      │ │
│ │   └──────────────────────────────┘      │ │
│ │                                          │ │
│ │ Write Count: [  0  ]                    │ │
│ │ Compression: [Hardware ▼]               │ │
│ └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### When "Disk" Selected
```
┌─────────────────────────────────────────────┐
│ Media Type: [Disk (HDD/SSD) ▼]             │
│                                             │
│ ┌── Disk-Specific Settings ──────────────┐ │
│ │ 💾 Interface Type                       │ │
│ │   ┌──────────────────────────────┐      │ │
│ │   │ SAS ▼                        │      │ │
│ │   └──────────────────────────────┘      │ │
│ │                                          │ │
│ │ ⚡ RPM                                   │ │
│ │   ┌──────────────────────────────┐      │ │
│ │   │ 7,200 RPM ▼                  │      │ │
│ │   └──────────────────────────────┘      │ │
│ │                                          │ │
│ │ Form Factor: [3.5" ▼]                   │ │
│ │ RAID Support: [Yes ▼]                   │ │
│ └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### When "Cloud" Selected
```
┌─────────────────────────────────────────────┐
│ Media Type: [Cloud Storage ▼]              │
│                                             │
│ ┌── Cloud-Specific Settings ─────────────┐ │
│ │ ☁️ Provider                             │ │
│ │   ┌──────────────────────────────┐      │ │
│ │   │ AWS S3 ▼                     │      │ │
│ │   └──────────────────────────────┘      │ │
│ │                                          │ │
│ │ 📦 Storage Class                        │ │
│ │   ┌──────────────────────────────┐      │ │
│ │   │ Glacier ▼                    │      │ │
│ │   └──────────────────────────────┘      │ │
│ │                                          │ │
│ │ Region: [ap-northeast-1]                │ │
│ │ Bucket: [backup-storage-prod]           │ │
│ └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Animation:** Smooth fade-in (300ms) when fields appear

---

## 5. Live Preview Card

```
┌─────────────────────────────────────────────┐
│ Media Label Preview                         │
│                                             │
│ ┌───────────────────────────────────────┐   │
│ │ ┌────┐                                │   │
│ │ │ QR │  LTO-123456                    │   │  ← Media ID (bold)
│ │ │Code│  営業部バックアップ用              │   │  ← Label name
│ │ └────┘  テープ (LTO)                   │   │  ← Media type
│ │         12 TB                          │   │  ← Capacity
│ │────────────────────────────────────────│   │
│ │ 本社ビル-1F-R1          2025/11/02     │   │  ← Location + Date
│ └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Updates In Real-Time:**
- ✅ Media ID
- ✅ Label Name
- ✅ Media Type
- ✅ Capacity (with unit)
- ✅ Location
- ✅ Mini QR Code (80×80px)
- ✅ Current Date (auto)

**Styling:**
- Blue border
- Box shadow
- Print-ready design

---

## Component Interactions Flowchart

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       ├─► Media ID ────────────► QR Code Generator ─────► Live Preview
       │                          (instant)
       │
       ├─► Capacity Value ───────► Unit Converter ────────► Visual Bar
       │                          GB ↔ TB                  (percentage)
       │
       ├─► Media Type ───────────► Wizard Fields ─────────► Auto-fill
       │                          Show/Hide                (ID, Capacity)
       │
       ├─► Location ─────────────► Cascading Dropdowns ───► Visual Map
       │                          Building→Floor→Rack
       │
       └─► All Fields ───────────► Live Preview Card ─────► Summary
                                   (real-time sync)
```

---

## Responsive Behavior

### Desktop (≥992px)
```
┌──────────────────────────────────┬──────────────┐
│                                  │              │
│  Main Form (col-lg-8)            │  Preview     │
│  ┌────────────────────────┐      │  Panel       │
│  │ Basic Info             │      │  (col-lg-4)  │
│  │ [Fields]               │      │              │
│  └────────────────────────┘      │  Sticky!     │
│  ┌────────────────────────┐      │              │
│  │ Technical Details      │      │              │
│  │ [Type-specific fields] │      │              │
│  └────────────────────────┘      │              │
│                                  │              │
└──────────────────────────────────┴──────────────┘
```

### Tablet/Mobile (<992px)
```
┌──────────────────────────────────┐
│  Preview Panel                   │
│  (stacks on top)                 │
└──────────────────────────────────┘
┌──────────────────────────────────┐
│  Main Form                       │
│  (full width)                    │
│                                  │
└──────────────────────────────────┘
```

---

## Color Scheme

### Status Colors
- 🟢 **Success/Available**: `#28a745`
- 🔴 **Danger/Occupied**: `#dc3545`
- 🟡 **Warning**: `#ffc107`
- 🔵 **Primary**: `#0d6efd`
- ⚫ **Secondary**: `#6c757d`

### UI Elements
- **Borders**: `#dee2e6`
- **Background**: `#f8f9fa`
- **Text Muted**: `#6c757d`
- **Hover**: `#e7f1ff`

---

## Keyboard Shortcuts (Future Enhancement)

| Key | Action |
|-----|--------|
| `Ctrl + S` | Submit form |
| `Ctrl + P` | Print QR code |
| `Ctrl + D` | Download QR code |
| `Tab` | Navigate fields |
| `Enter` | Select dropdown option |
| `Esc` | Close dialogs |

---

## Animation Timing

| Element | Duration | Easing |
|---------|----------|--------|
| Field Show/Hide | 300ms | ease |
| Capacity Bar | 300ms | ease |
| Hover Effects | 200ms | ease |
| QR Generation | 100ms | linear |

---

## Browser DevTools Tips

### Test QR Code Generation
```javascript
// Console command to test QR generation
document.getElementById('media_id').value = 'TEST-12345';
document.getElementById('media_id').dispatchEvent(new Event('input'));
```

### Test Capacity Calculator
```javascript
// Set capacity to 5TB
document.getElementById('capacity_value').value = 5;
document.getElementById('capacity_unit').value = 'tb';
updateCapacity();
```

### Test Location Picker
```javascript
// Select location programmatically
document.getElementById('building_select').value = '本社ビル';
document.getElementById('building_select').dispatchEvent(new Event('change'));
```

---

## Accessibility Features

### Screen Reader Labels
```html
<!-- Example: Capacity slider -->
<input type="range"
       aria-label="Capacity slider from 0GB to 20TB"
       aria-valuemin="0"
       aria-valuemax="20480"
       aria-valuenow="1000">
```

### Keyboard Navigation
- All interactive elements are focusable
- Visual focus indicators
- Logical tab order
- Enter key activates buttons

### ARIA Attributes
- `aria-required="true"` on required fields
- `aria-invalid="true"` on validation errors
- `aria-describedby` for helper text
- `role="alert"` for error messages

---

## Print Stylesheet (QR Code)

```css
@media print {
  .qr-print-layout {
    text-align: center;
    padding: 20mm;
  }

  .qr-print-layout img {
    width: 100mm;
    height: 100mm;
  }

  .qr-print-label {
    font-size: 24pt;
    font-weight: bold;
    margin: 10mm 0;
  }
}
```

---

## Component Dependencies

```
Bootstrap 5
    └── Grid System (col-*, row)
    └── Form Controls (form-control, form-select)
    └── Buttons (btn, btn-primary, btn-secondary)
    └── Cards (card, card-header, card-body)
    └── Utilities (mb-3, mt-2, d-flex, etc.)

QRCode.js (CDN)
    └── QR Code generation
    └── Canvas rendering
    └── PNG export

Custom JavaScript
    └── Capacity Calculator
    └── Location Picker
    └── Media Type Wizard
    └── Live Preview Sync

Custom CSS
    └── Visual capacity bar
    └── Rack grid layout
    └── Type-specific field animations
    └── Media label preview card
```

---

**Component Guide Version:** 1.0.0
**Last Updated:** November 2, 2025
**Maintained By:** Agent-06 (UI/UX Specialist)
