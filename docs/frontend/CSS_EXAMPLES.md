# CSS Examples: Before & After Conversions

## 🎯 Overview

This document shows practical examples of converting from mixed Tailwind/Custom CSS to our hybrid approach: **Tailwind for layout, Custom CSS for design**.

## 📋 Example 1: Page Header

### ❌ **Before (Mixed Approach)**
```html
<div class="bg-gradient-to-r from-green-400 to-blue-500 rounded-xl p-8 mb-8">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-white mb-2">Dashboard</h1>
      <p class="text-white opacity-90">Welcome to your workspace</p>
    </div>
    <button class="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition-colors">
      New Project
    </button>
  </div>
</div>
```

### ✅ **After (Hybrid Approach)**
```html
<div class="page-header scientific-accent mb-8">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-heading text-inverse mb-2">Dashboard</h1>
      <p class="text-body text-inverse opacity-90">Welcome to your workspace</p>
    </div>
    <button class="btn btn-primary">New Project</button>
  </div>
</div>
```

**What changed:**
- **Layout**: Kept `flex items-center justify-between` (Tailwind)
- **Design**: Converted to `page-header scientific-accent` (Custom CSS)
- **Typography**: Converted to `text-heading text-body` (Custom CSS)
- **Button**: Converted to `btn btn-primary` (Custom CSS)

## 📋 Example 2: Card Component

### ❌ **Before (Mixed Approach)**
```html
<div class="bg-white rounded-lg shadow-md p-6 border border-gray-200 mb-6">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-xl font-semibold text-gray-900">Project Statistics</h3>
    <span class="px-2 py-1 bg-green-100 text-green-800 text-sm rounded-full">Active</span>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="text-center">
      <div class="text-2xl font-bold text-blue-600">12</div>
      <div class="text-sm text-gray-600">Active Projects</div>
    </div>
    <div class="text-center">
      <div class="text-2xl font-bold text-green-600">8</div>
      <div class="text-sm text-gray-600">Completed</div>
    </div>
    <div class="text-center">
      <div class="text-2xl font-bold text-orange-600">4</div>
      <div class="text-sm text-gray-600">In Progress</div>
    </div>
  </div>
</div>
```

### ✅ **After (Hybrid Approach)**
```html
<div class="card card-elevated mb-6">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-subheading">Project Statistics</h3>
    <span class="status-badge status-active">Active</span>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="text-center">
      <div class="stat-value stat-primary">12</div>
      <div class="stat-label">Active Projects</div>
    </div>
    <div class="text-center">
      <div class="stat-value stat-success">8</div>
      <div class="stat-label">Completed</div>
    </div>
    <div class="text-center">
      <div class="stat-value stat-warning">4</div>
      <div class="stat-label">In Progress</div>
    </div>
  </div>
</div>
```

**What changed:**
- **Layout**: Kept `flex items-center justify-between`, `grid grid-cols-1 md:grid-cols-3 gap-4` (Tailwind)
- **Design**: Converted to `card card-elevated` (Custom CSS)
- **Typography**: Converted to `text-subheading`, `stat-value`, `stat-label` (Custom CSS)
- **Colors**: Converted to `stat-primary`, `stat-success`, `stat-warning` (Custom CSS)
- **Status**: Converted to `status-badge status-active` (Custom CSS)

## 📋 Example 3: Form Component

### ❌ **Before (Mixed Approach)**
```html
<form class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
  <div class="mb-4">
    <label class="block text-sm font-medium text-gray-700 mb-1">
      Project Name <span class="text-red-500">*</span>
    </label>
    <input 
      type="text" 
      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      placeholder="Enter project name"
    >
    <p class="mt-1 text-sm text-red-600">Project name is required</p>
  </div>
  
  <div class="flex justify-end gap-4 pt-6 border-t border-gray-200">
    <button type="button" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors">
      Cancel
    </button>
    <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
      Create Project
    </button>
  </div>
</form>
```

### ✅ **After (Hybrid Approach)**
```html
<form class="form-container">
  <div class="form-group">
    <label class="form-label">
      Project Name <span class="text-danger">*</span>
    </label>
    <input 
      type="text" 
      class="form-input"
      placeholder="Enter project name"
    >
    <p class="form-error">Project name is required</p>
  </div>
  
  <div class="flex justify-end gap-4 pt-6 border-t border-light">
    <button type="button" class="btn btn-secondary">Cancel</button>
    <button type="submit" class="btn btn-primary">Create Project</button>
  </div>
</form>
```

**What changed:**
- **Layout**: Kept `flex justify-end gap-4 pt-6` (Tailwind)
- **Design**: Converted to `form-container`, `form-group` (Custom CSS)
- **Form Elements**: Converted to `form-label`, `form-input`, `form-error` (Custom CSS)
- **Buttons**: Converted to `btn btn-secondary`, `btn btn-primary` (Custom CSS)
- **Colors**: Converted to `text-danger`, `border-light` (Custom CSS)

## 📋 Example 4: Navigation Component

### ❌ **Before (Mixed Approach)**
```html
<nav class="bg-gray-900 border-b border-gray-800">
  <div class="max-w-7xl mx-auto px-4">
    <div class="flex items-center justify-between h-16">
      <div class="flex items-center">
        <h1 class="text-xl font-bold text-white">LMS Evo</h1>
      </div>
      
      <div class="flex items-center space-x-4">
        <a href="/dashboard" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
          Dashboard
        </a>
        <a href="/projects" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
          Projects
        </a>
        <button class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium">
          New Project
        </button>
      </div>
    </div>
  </div>
</nav>
```

### ✅ **After (Hybrid Approach)**
```html
<nav class="navbar">
  <div class="container mx-auto px-4">
    <div class="flex items-center justify-between h-16">
      <div class="flex items-center">
        <h1 class="brand-text">LMS Evo</h1>
      </div>
      
      <div class="flex items-center space-x-4">
        <a href="/dashboard" class="nav-link">Dashboard</a>
        <a href="/projects" class="nav-link">Projects</a>
        <button class="btn btn-primary">New Project</button>
      </div>
    </div>
  </div>
</nav>
```

**What changed:**
- **Layout**: Kept `flex items-center justify-between h-16`, `space-x-4` (Tailwind)
- **Design**: Converted to `navbar`, `brand-text`, `nav-link` (Custom CSS)
- **Button**: Converted to `btn btn-primary` (Custom CSS)
- **Container**: Kept `container mx-auto px-4` (Tailwind)

## 🎯 Key Patterns

### **Layout Patterns (Keep Tailwind)**
```html
<!-- Container layouts -->
<div class="container mx-auto px-4 py-8">

<!-- Flexbox layouts -->
<div class="flex items-center justify-between">

<!-- Grid layouts -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

<!-- Spacing -->
<div class="p-6 mb-8 mt-4 space-x-4">

<!-- Responsive -->
<div class="md:grid-cols-2 lg:flex-row">
```

### **Design Patterns (Use Custom CSS)**
```html
<!-- Typography -->
<h1 class="text-heading">Title</h1>
<p class="text-body">Content</p>

<!-- Colors -->
<div class="text-primary bg-elevated border-light">

<!-- Components -->
<button class="btn btn-primary">Action</button>
<div class="card card-elevated">Content</div>
<input class="form-input" type="text">

<!-- Interactive States -->
<button class="btn btn-primary">Hover built-in</button>
```

## 🚀 Benefits Demonstrated

1. **Cleaner HTML**: Semantic classes instead of utility combinations
2. **Consistent Design**: All design elements use the design system
3. **Maintainable**: Changes to design system automatically apply
4. **Flexible Layout**: Tailwind's excellent layout utilities remain
5. **Clear Intent**: Easy to understand what's layout vs design

## 📝 Conversion Checklist

When converting any component:

- [ ] **Identify layout utilities** (keep as Tailwind)
- [ ] **Identify design elements** (convert to custom CSS)
- [ ] **Map colors** to design system variables
- [ ] **Map typography** to semantic classes
- [ ] **Use component classes** for buttons, cards, forms
- [ ] **Test responsive behavior** still works
- [ ] **Verify visual consistency** with design system
