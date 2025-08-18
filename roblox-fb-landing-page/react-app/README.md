# Roblox Safety Platform - React Application

A React-based web application for protecting children in online gaming environments, converted from HTML templates to a fully functional React app with routing.

## Features

- **Responsive Design**: Mobile-first approach with Bootstrap 5
- **React Router**: Clean routing structure with `/roblox/parent` and `/roblox/child` routes
- **Form Validation**: Real-time validation with error handling
- **Modal Integration**: Bootstrap modal for success messages
- **Phone Number Formatting**: Auto-formatting for US phone numbers
- **Animated Thank You Page**: Confetti animation and smooth transitions
- **Google Analytics**: Integrated GTM and GA4 tracking

## Routes

- `/roblox/parent` - Parents landing page with comprehensive form
- `/roblox/child` - Kids-friendly page with simplified form
- `/roblox/thank-you` - Success page with animations
- `/roblox/` - Redirects to parent page

## Project Structure

```
src/
├── components/
│   ├── SuccessModal.js     # Reusable modal component
│   └── Footer.js           # Footer component
├── pages/
│   ├── ParentsPage.js      # Main parents landing page
│   ├── KidsPage.js         # Kids-friendly page
│   └── ThankYouPage.js     # Success/thank you page
├── assets/
│   ├── css/
│   │   └── style.css       # Main stylesheet (converted from original)
│   └── img/                # All images from original template
├── App.js                  # Main app with routing
└── index.js               # React entry point
```

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   cd react-app
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm start
   ```
   The app will be available at `http://localhost:3000/roblox`

3. **Build for Production**:
   ```bash
   npm run build
   ```

## Key Components

### ParentsPage
- Comprehensive form with 5 fields (name, email, phone, state, description)
- Phone number auto-formatting with US format validation
- Email validation
- Form error handling with visual feedback
- Multiple content sections explaining services

### KidsPage
- Simplified form for children (name, email, description only)
- Kid-friendly language and design
- Hero background with gaming theme
- Safety tips and guidelines

### ThankYouPage
- Animated confetti effect
- Inline styles for complete self-containment
- Navigation back to main pages
- Responsive design

### SuccessModal
- Reusable Bootstrap modal
- Automatic redirect to thank you page
- Consistent styling across pages

## Form Handling

Both forms include:
- Real-time validation
- Error state management
- Form reset after successful submission
- Modal confirmation before redirect
- Proper form accessibility (labels, ARIA attributes)

## Styling

- Original CSS maintained and adapted for React
- Bootstrap 5 for responsive grid and components
- Custom animations and gradients
- Mobile-optimized media queries
- Poppins font family integration

## Analytics

The application includes:
- Google Analytics 4 (GA4) tracking
- Google Tag Manager (GTM) integration
- Event tracking capabilities

## Browser Support

- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Deployment

The app is configured with `"homepage": "/roblox"` for deployment under a subdirectory. For different deployment scenarios:

1. **Root domain**: Remove `basename="/roblox"` from App.js and `homepage` from package.json
2. **Different subdirectory**: Update both `homepage` in package.json and `basename` in App.js
3. **Build**: Run `npm run build` and deploy the `build` folder contents

## Development Notes

- All original functionality has been preserved
- Form submission currently shows modal and redirects (backend integration ready)
- Images are optimized and properly imported
- CSS classes maintain original naming for consistency
- Google Analytics and GTM codes are included and ready for production
