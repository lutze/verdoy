# CSS Quick Reference: Tailwind vs Custom CSS

## 🎯 Quick Decision Tree

**Ask yourself: "What am I styling?"**

- **Layout/Spacing** → Use **Tailwind**
- **Design/Branding** → Use **Custom CSS**

## 📋 Tailwind Usage (Layout & Spacing)

### ✅ **Use Tailwind For:**

```html
<!-- Layout -->
<div class="container mx-auto px-4 py-8">
<div class="flex items-center justify-between">
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

<!-- Spacing -->
<div class="p-6 mb-8 mt-4">
<div class="space-x-4 space-y-6">
<div class="gap-4">

<!-- Sizing -->
<div class="w-full h-16 max-w-4xl">
<div class="w-5 h-5">

<!-- Responsive -->
<div class="md:grid-cols-2 lg:flex-row">
<div class="sm:hidden md:block">

<!-- Basic Utils -->
<div class="relative overflow-hidden z-10">
<div class="block hidden">
```

## 🎨 Custom CSS Usage (Design & Branding)

### ✅ **Use Custom CSS For:**

```html
<!-- Colors (Design System) -->
<div class="text-primary bg-elevated border-light">
<div class="text-secondary bg-subtle">

<!-- Typography -->
<h1 class="text-heading">Title</h1>
<p class="text-body">Content</p>
<span class="text-caption">Small text</span>

<!-- Components -->
<button class="btn btn-primary">Action</button>
<div class="card card-elevated">Content</div>
<input class="form-input" type="text">

<!-- Interactive States -->
<button class="btn btn-primary">Hover effect built-in</button>
<input class="form-input">Focus effect built-in</input>

<!-- Scientific Theme -->
<div class="scientific-accent">Gradient background</div>
<div class="glass">Glassmorphism effect</div>
```

## 🚫 What NOT to Mix

### ❌ **Avoid These Combinations:**

```html
<!-- DON'T: Mix Tailwind design with custom layout -->
<div class="bg-white rounded-lg shadow-md p-6">  <!-- Tailwind design -->
  <button class="btn btn-primary">Custom button</button>  <!-- Custom design -->
</div>

<!-- DON'T: Use Tailwind colors -->
<div class="text-gray-900 bg-blue-600 border-gray-300">

<!-- DON'T: Use Tailwind typography -->
<h1 class="text-3xl font-bold text-gray-900">

<!-- DON'T: Use Tailwind shadows -->
<div class="shadow-sm shadow-md shadow-lg">
```

## ✅ **Good Examples**

```html
<!-- ✅ Layout with Tailwind, Design with Custom CSS -->
<div class="container mx-auto px-4 py-8">
  <div class="page-header scientific-accent mb-8">
    <h1 class="text-heading">Dashboard</h1>
  </div>
  
  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div class="card card-elevated">
      <h3 class="text-subheading">Title</h3>
      <p class="text-body">Content</p>
    </div>
  </div>
  
  <div class="flex justify-end gap-4 mt-8">
    <button class="btn btn-secondary">Cancel</button>
    <button class="btn btn-primary">Save</button>
  </div>
</div>
```

## 🎯 Key Principles

1. **Tailwind = Layout & Spacing**
2. **Custom CSS = Design & Branding**
3. **Never mix design approaches in same component**
4. **Use design system colors, not Tailwind colors**
5. **Use semantic component classes, not utility combinations**

## 🔧 Common Patterns

### **Page Layout**
```html
<div class="container mx-auto px-4 py-8">
  <div class="page-header mb-8">
    <h1 class="text-heading">Page Title</h1>
  </div>
  
  <div class="content-section">
    <!-- Content here -->
  </div>
</div>
```

### **Card Component**
```html
<div class="card card-elevated">
  <div class="card-header">
    <h3 class="text-subheading">Card Title</h3>
  </div>
  <div class="card-content">
    <p class="text-body">Card content</p>
  </div>
</div>
```

### **Form Component**
```html
<form class="form-container">
  <div class="form-group">
    <label class="form-label">Field Label</label>
    <input class="form-input" type="text">
  </div>
  <div class="flex justify-end gap-4">
    <button class="btn btn-secondary">Cancel</button>
    <button class="btn btn-primary">Submit</button>
  </div>
</form>
```

## 📚 Need Help?

- **Full Guidelines**: See `CSS_USAGE_GUIDELINES.md`
- **Design System**: See `DESIGN_SYSTEM.md`
- **Components**: See `COMPONENTS.md`
