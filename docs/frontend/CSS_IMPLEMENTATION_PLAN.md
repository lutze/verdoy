# CSS Implementation Plan: Hybrid Approach

## 🎯 Goal

Establish a clear separation between Tailwind (layout) and Custom CSS (design) while minimizing disruption to the existing codebase.

## 📋 Implementation Strategy

### **Phase 1: Foundation (1-2 days)**

#### **1.1 Create Missing Design System Classes**
Add these classes to `components.css` to support the guidelines:

```css
/* Typography Classes */
.text-heading {
  font-size: var(--font-size-4xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.25;
}

.text-subheading {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.25;
}

.text-body {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  line-height: 1.6;
}

.text-caption {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

/* Layout Classes */
.page-header {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  margin-bottom: var(--space-6);
  position: relative;
  overflow: hidden;
}

.content-section {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--border-light);
}

/* Component Classes */
.card-elevated {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-light);
  padding: var(--space-6);
}

.card-interactive {
  transition: all var(--transition-normal);
}

.card-interactive:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```

#### **1.2 Update Existing Components**
Ensure these existing classes follow the guidelines:

- ✅ `btn`, `btn-primary`, `btn-secondary` (already good)
- ✅ `card` (already good)
- ✅ `form-input`, `form-label` (already good)
- ✅ `page-header` (already good)

### **Phase 2: High-Impact Conversions (2-3 days)**

#### **2.1 Convert Button Styling (Priority: High)**
**Target**: All button elements across templates

**Current (Tailwind design)**:
```html
<button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
```

**Target (Custom design)**:
```html
<button class="btn btn-primary">
```

**Files to update**:
- `pages/experiments/monitor.html`
- `pages/experiments/edit.html`
- `pages/processes/edit.html`
- `pages/organizations/invitation.html`

#### **2.2 Convert Card Styling (Priority: High)**
**Target**: All card-like containers

**Current (Tailwind design)**:
```html
<div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
```

**Target (Custom design)**:
```html
<div class="card card-elevated">
```

**Files to update**:
- `pages/experiments/monitor.html`
- `pages/experiments/edit.html`
- `pages/processes/edit.html`
- `pages/organizations/invitation.html`

#### **2.3 Convert Form Styling (Priority: Medium)**
**Target**: Form inputs and labels

**Current (Tailwind design)**:
```html
<input class="w-full px-3 py-2 border border-gray-300 rounded-md">
```

**Target (Custom design)**:
```html
<input class="form-input">
```

### **Phase 3: Color System Migration (1-2 days)**

#### **3.1 Replace Tailwind Colors with Design System Colors**

**Color Mapping**:
- `text-gray-900` → `text-primary`
- `text-gray-600` → `text-secondary`
- `text-gray-500` → `text-tertiary`
- `bg-white` → `bg-elevated`
- `bg-gray-50` → `bg-subtle`
- `border-gray-300` → `border-light`
- `border-gray-200` → `border-light`

**Files to update**:
- `pages/experiments/monitor.html`
- `pages/experiments/edit.html`
- `pages/processes/edit.html`
- `pages/organizations/invitation.html`
- `pages/error.html`

#### **3.2 Replace Status Colors**
**Color Mapping**:
- `text-red-500` → `text-danger`
- `text-green-600` → `text-success`
- `text-blue-600` → `text-info`
- `text-yellow-500` → `text-warning`

### **Phase 4: Typography Migration (1 day)**

#### **4.1 Replace Tailwind Typography**

**Typography Mapping**:
- `text-3xl font-bold` → `text-heading`
- `text-xl font-semibold` → `text-subheading`
- `text-lg font-semibold` → `text-subheading`
- `text-sm font-medium` → `text-caption`
- `text-sm` → `text-caption`

### **Phase 5: Gradual Migration (Ongoing)**

#### **5.1 Template-by-Template Approach**
When working on any template:

1. **Keep Tailwind for**:
   - Layout containers (`container`, `mx-auto`)
   - Flexbox (`flex`, `items-center`)
   - Grid (`grid`, `grid-cols-1`)
   - Spacing (`p-4`, `mb-8`, `gap-6`)
   - Responsive (`md:grid-cols-2`)

2. **Convert to Custom CSS**:
   - Colors (use design system colors)
   - Typography (use semantic classes)
   - Components (use component classes)
   - Interactive states (use custom hover/focus)

#### **5.2 Component-First Approach**
When creating new components:

1. **Start with layout** (Tailwind)
2. **Add design** (Custom CSS)
3. **Test both approaches** work together

## 🎯 Success Metrics

### **Phase 1 Success**:
- [ ] Guidelines documented
- [ ] Missing CSS classes added
- [ ] Team understands the approach

### **Phase 2 Success**:
- [ ] All buttons use `btn` classes
- [ ] All cards use `card` classes
- [ ] All forms use `form-*` classes

### **Phase 3 Success**:
- [ ] No Tailwind colors in templates
- [ ] All colors use design system variables
- [ ] Consistent color usage across components

### **Phase 4 Success**:
- [ ] No Tailwind typography in templates
- [ ] All text uses semantic typography classes
- [ ] Consistent typography hierarchy

### **Phase 5 Success**:
- [ ] Clear separation maintained
- [ ] New templates follow guidelines
- [ ] Team follows guidelines consistently

## 🚀 Quick Wins (Can do today)

### **1. Update One Template as Example**
Pick one template (e.g., `pages/error.html`) and convert it completely to demonstrate the approach.

### **2. Create Component Examples**
Add examples to the documentation showing before/after conversions.

### **3. Team Training**
Share the quick reference with the team and explain the approach.

## 📝 Template Conversion Checklist

When converting a template, check:

- [ ] **Layout**: Keep Tailwind utilities (`container`, `flex`, `grid`)
- [ ] **Spacing**: Keep Tailwind utilities (`p-4`, `mb-8`, `gap-6`)
- [ ] **Colors**: Convert to design system colors
- [ ] **Typography**: Convert to semantic classes
- [ ] **Components**: Use component classes (`btn`, `card`, `form-*`)
- [ ] **Interactive**: Use custom hover/focus states
- [ ] **Responsive**: Keep Tailwind responsive utilities
- [ ] **Test**: Verify layout and design work together

## 🎯 Benefits of This Approach

1. **Immediate**: Clear guidelines for team
2. **Short-term**: Consistent design system usage
3. **Long-term**: Maintainable, semantic codebase
4. **Performance**: Smaller custom CSS bundle
5. **Flexibility**: Best of both worlds

## 📚 Resources

- **Guidelines**: `CSS_USAGE_GUIDELINES.md`
- **Quick Reference**: `CSS_QUICK_REFERENCE.md`
- **Design System**: `DESIGN_SYSTEM.md`
- **Components**: `COMPONENTS.md`
