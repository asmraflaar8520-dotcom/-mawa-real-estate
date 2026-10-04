---
name: My Design System
colors:
  surface: '#f9f9ff'
  surface-dim: '#d7dae3'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3fc'
  surface-container: '#ebedf7'
  surface-container-high: '#e6e8f1'
  surface-container-highest: '#e0e2eb'
  on-surface: '#181c22'
  on-surface-variant: '#414753'
  inverse-surface: '#2d3037'
  inverse-on-surface: '#eef0fa'
  outline: '#717785'
  outline-variant: '#c1c6d5'
  surface-tint: '#005db8'
  primary: '#005cb8'
  on-primary: '#ffffff'
  primary-container: '#1275e2'
  on-primary-container: '#000512'
  inverse-primary: '#aac7ff'
  secondary: '#465f88'
  on-secondary: '#ffffff'
  secondary-container: '#b6d0ff'
  on-secondary-container: '#3f5881'
  tertiary: '#9a4600'
  on-tertiary: '#ffffff'
  tertiary-container: '#c05900'
  on-tertiary-container: '#0d0300'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#aac7ff'
  on-primary-fixed: '#001b3e'
  on-primary-fixed-variant: '#00458d'
  secondary-fixed: '#d6e3ff'
  secondary-fixed-dim: '#aec7f7'
  on-secondary-fixed: '#001b3d'
  on-secondary-fixed-variant: '#2d476f'
  tertiary-fixed: '#ffdbc9'
  tertiary-fixed-dim: '#ffb68c'
  on-tertiary-fixed: '#321200'
  on-tertiary-fixed-variant: '#763400'
  background: '#f9f9ff'
  on-background: '#181c22'
  surface-variant: '#e0e2eb'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

# Design System

## Brand & Style
The design system adopts a **Corporate / Modern** style, emphasizing reliability, balanced visual hierarchy, and professional clarity. It uses the **Inter** font family across all typography levels to ensure pristine readability and a contemporary digital feel. The aesthetic relies on clean layouts, structured surfaces, and a purposeful color palette.

## Colors
The color palette is built for clarity and semantic precision under a **light** color mode:
- **Primary Color (`#1275e2`)**: A dependable, vibrant blue used for key interactive elements, primary actions, and focus states.
- **Secondary Color (`#5f78a3`)**: A slate blue-gray providing balanced support for secondary actions and subtle containers.
- **Tertiary Color (`#c55b00`)**: A warm amber-orange accent used for highlights, alerts, and calls to action.
- **Neutral Color (`#74777f`)**: A versatile cool gray utilized for structural surfaces, borders, and body text.

## Typography
The typography system relies exclusively on **Inter** for all headlines, body copy, and labels, ensuring a unified geometric rhythm. Type scales dynamically from crisp micro-labels up to prominent headlines, optimized for both dense data displays and spacious marketing layouts.

## Layout & Spacing
Using a responsive fluid grid model with 1rem gutters and 1.5rem outer margins, the layout adapts smoothly from mobile devices to desktop viewports. The spacing scale (`space-xs` through `space-xl`) provides consistent rhythm for component padding and internal element gaps.

## Elevation & Depth
Visual hierarchy is achieved primarily through tonal surface layers and clean, low-contrast outlines. Subtle structural borders paired with minimal ambient shadows establish distinct containment without visual clutter.

## Shapes
The shape language uses a **Rounded** scale (`roundedness: 2`), featuring standard 0.5rem corner radii for buttons and inputs, scaling up to 1rem (`rounded-lg`) and 1.5rem (`rounded-xl`) for larger cards and containers to create a friendly, modern feel.

## Components
- **Buttons**: Feature solid primary or secondary fills with rounded corners (`0.5rem`), clear Inter label typography, and high-contrast focus rings.
- **Chips**: Compact tagging elements utilizing neutral or tinted backgrounds with soft rounded edges.
- **Input Fields**: Clean outlined or filled text boxes featuring the designated neutral borders and primary focus states.
- **Cards**: Surface containers utilizing rounded corners, subtle tonal separation, and clear internal padding based on the spacing scale.