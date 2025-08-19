# CSS Usage Guidelines: Tailwind vs Custom CSS

## Overview

This document establishes clear guidelines for when to use Tailwind CSS utility classes versus custom CSS classes in the LMS evo platform. This hybrid approach gives us the best of both worlds: Tailwind's layout utilities and our custom design system.

## 🎯 Core Principle

**Use Tailwind for layout and spacing, Custom CSS for design and branding.**

## 📋 Usage Rules

### ✅ **Use Tailwind CSS For:**

#### **Layout & Structure**
- Container layouts: `container`, `mx-auto`
- Flexbox: `flex`, `items-center`, `justify-between`, `justify-center`
- Grid: `grid`, `grid-cols-1`, `md:grid-cols-2`, `lg:grid-cols-3`
- Display: `block`, `hidden`, `inline`, `inline-block`

#### **Spacing & Positioning**
- Padding: `p-4`, `px-6`, `py-8`, `pt-4`, `pb-6`
- Margin: `m-4`, `mx-auto`, `my-6`, `mt-8`, `mb-4`
- Gap: `gap-4`, `gap-6`, `space-x-4`, `space-y-6`
- Width/Height: `w-full`, `w-16`, `h-8`, `max-w-4xl`

#### **Responsive Design**
- Breakpoint prefixes: `sm:`, `md:`, `lg:`, `xl:`
- Responsive layouts: `md:grid-cols-2`, `lg:flex-row`

#### **Basic Utilities**
- Overflow: `overflow-hidden`, `overflow-auto`
- Position: `relative`, `absolute`, `fixed`
- Z-index: `z-10`, `z-50`

### ✅ **Use Custom CSS For:**

#### **Brand Identity & Design**
- **Colors**: Use design system colors, not Tailwind colors
  - ✅ `text-primary`, `bg-elevated`, `border-light`
  - ❌ `text-gray-900`, `bg-blue-600`, `border-gray-300`

- **Typography**: Use design system typography
  - ✅ `text-heading`, `text-body`, `font-brand`
  - ❌ `text-2xl`, `font-bold`, `text-sm`

- **Shadows & Effects**: Use design system shadows
  - ✅ `shadow-md`, `shadow-lg` (our custom versions)
  - ❌ `shadow-sm`, `shadow-xl` (Tailwind versions)

#### **Component Styling**
- **Buttons**: Use semantic button classes
  - ✅ `btn`, `btn-primary`, `btn-secondary`
  - ❌ `px-4 py-2 bg-blue-600 text-white rounded`

- **Cards**: Use semantic card classes
  - ✅ `card`, `card-elevated`, `card-interactive`
  - ❌ `bg-white rounded-lg shadow-md p-6`

- **Forms**: Use semantic form classes
  - ✅ `form-input`, `form-label`, `form-error`
  - ❌ `w-full px-3 py-2 border border-gray-300 rounded`

#### **Interactive States**
- **Hover/Focus**: Use custom state classes
  - ✅ `btn:hover`, `form-input:focus`
  - ❌ `hover:bg-blue-700`, `focus:ring-2`

- **Transitions**: Use design system transitions
  - ✅ `transition-normal`, `transition-fast`
  - ❌ `transition-colors`, `duration-300`

#### **Scientific Theme Elements**
- **Gradients**: Use brand gradients
  - ✅ `scientific-accent`, `gradient-primary`
  - ❌ `bg-gradient-to-r from-blue-500 to-purple-600`

- **Special Effects**: Use custom effects
  - ✅ `glass`, `organic-shape`
  - ❌ `backdrop-blur`, `filter`

## 🎨 Class Naming Conventions

### **Custom CSS Classes**
- **Components**: `btn`, `card`, `form-input`
- **Layout**: `page-header`, `content-section`, `sidebar`
- **States**: `active`, `disabled`, `loading`
- **Variants**: `btn-primary`, `card-elevated`, `text-heading`

### **Tailwind Classes**
- **Utilities**: `flex`, `p-4`, `w-full`
- **Responsive**: `md:grid-cols-2`, `lg:flex-row`
- **States**: `hover:`, `focus:`, `active:`

## 📝 Examples

### ✅ **Good Examples**

```html
<!-- Layout with Tailwind, Design with Custom CSS -->
<div class="container mx-auto px-4 py-8">
  <div class="page-header scientific-accent mb-8">
    <h1 class="text-heading">Dashboard</h1>
  </div>
  
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="card card-elevated">
      <div class="card-header">
        <h3 class="text-subheading">Statistics</h3>
      </div>
      <div class="card-content">
        <p class="text-body">Content here</p>
      </div>
    </div>
  </div>
  
  <div class="flex justify-end gap-4 mt-8">
    <button class="btn btn-secondary">Cancel</button>
    <button class="btn btn-primary">Save</button>
  </div>
</div>
```

### ❌ **Bad Examples**

```html
<!-- Mixing Tailwind design with custom layout -->
<div class="bg-white rounded-lg shadow-md p-6 mx-auto max-w-4xl">
  <h1 class="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
  
  <div class="flex items-center justify-between">
    <button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
      Action
    </button>
  </div>
</div>
```

## 🔧 Implementation Strategy

### **Phase 1: Establish Guidelines (1 day)**
1. Document these guidelines
2. Create a style guide for the team
3. Set up linting rules if possible

### **Phase 2: Convert High-Value Components (2-3 days)**
1. **Buttons**: Convert all button styling to custom classes
2. **Cards**: Create semantic card components
3. **Forms**: Standardize form styling
4. **Navigation**: Use custom navigation classes

### **Phase 3: Gradual Migration (ongoing)**
1. When touching a template, apply these guidelines
2. Convert design elements to custom CSS
3. Keep layout utilities as Tailwind
4. Test and refine

## 🎯 Benefits of This Approach

1. **Clear Separation**: No confusion about what to use when
2. **Brand Consistency**: All design elements use our design system
3. **Layout Flexibility**: Tailwind's excellent layout utilities
4. **Maintainability**: Semantic classes for components
5. **Performance**: Smaller custom CSS bundle
6. **Team Clarity**: Clear guidelines for all developers

## 🚫 What to Avoid

1. **Mixing approaches** in the same component
2. **Using Tailwind colors** instead of design system colors
3. **Creating custom utilities** that duplicate Tailwind
4. **Over-engineering** simple layouts

## 📚 Resources

- [Design System Documentation](./DESIGN_SYSTEM.md)
- [Component Library](./COMPONENTS.md)
- [Color Palette](./COLORS.md)
- [Typography Guide](./TYPOGRAPHY.md)
