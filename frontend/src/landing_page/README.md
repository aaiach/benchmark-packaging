# Landing Page Design System

This directory contains the design system and components specifically for the Landing Page of the Packaging Benchmarking Tool.

## Design Philosophy
**Minimalist Ultra Glassmorphism**
- **Light Mode** primarily (White/Black).
- Heavy use of **translucency**, **blur**, and **subtle shadows**.
- **Ambient Orbs** for background using specific pastel colors.

## Color Palette (Ambient Orbs)
- Base: `#c3dafe` (Light Blue)
- Light Orange: `#ffb07a`
- Cyan: `#1feeff`
- Pale Pink: `#ffdbde`
- Hot Pink: `#ff85b3`
- Coral: `#ff8a52`
- Soft Blue/Purple: `#6666ff`
- Pink: `#ff85a3`

## Typography
- Minimalist sans-serif for body text.
- Grayscale highlights (italic, reduced opacity) for emphasis instead of bold colors.

## Components
- `AmbientBackground`: Animated background with colorful orbs.
- `GlassCard`: Card component with glassmorphism effect (blur, semi-transparent white background, border).
- `GlassButton`: Buttons with glass effect or solid black for primary actions.
- `GlassInput`: Input fields with glass effect.

## Structure
- `components/`: Reusable UI components for the landing page.
- `LandingPage.tsx`: The main landing page composition.
