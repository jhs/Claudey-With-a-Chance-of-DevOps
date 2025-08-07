# CLAUDE.md - UI Application Guide

## Overview

The UI application is a Next.js web application that provides a web interface for the Claudey With a Chance of DevOps (CWCD) project. It integrates CopilotKit for AI-powered DevOps assistance through a conversational sidebar interface.

## Project Structure

```
ui/
├── package.json         # Next.js project configuration
├── tsconfig.json        # TypeScript configuration
├── next.config.ts       # Next.js configuration
├── postcss.config.mjs   # PostCSS configuration
├── src/
│   └── app/             # Next.js App Router
│       ├── layout.tsx   # Root layout with CopilotKit integration
│       ├── page.tsx     # Home page with VNC iframe
│       ├── globals.css  # Global styles with Tailwind CSS
│       └── api/
│           └── copilotkit/
│               └── route.ts # CopilotKit API endpoint
└── public/              # Static assets
    ├── *.svg            # Next.js default icons
    └── ...
```

## Technology Stack

### Core Framework
- **Next.js**: 15.4.4 - React framework with App Router
- **React**: 19.1.0 - UI library
- **TypeScript**: ^5 - Type safety and development experience
- **Tailwind CSS**: ^4 - Utility-first CSS framework

### AI Integration
- **CopilotKit**: ^1.9.3 - AI-powered conversational interface
  - `@copilotkit/react-core`: Core React integration
  - `@copilotkit/react-ui`: UI components including CopilotSidebar
  - `@copilotkit/runtime`: Runtime adapter for AI capabilities

### Styling
- **Geist Fonts**: Sans and mono font families from Next.js
- **CSS**: PostCSS with Tailwind CSS processing

## Key Components

### Root Layout (`src/app/layout.tsx`)

Provides the main application structure with CopilotKit integration:

```tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="font-geist">
        <CopilotKit runtimeUrl="/api/copilotkit">
          <CopilotSidebar
            defaultOpen={true}
            instructions="You are assisting the user as best as you can..."
            labels={{
              title: "Claudey With a Chance of DevOps",
              initial: "Let's talk DevOps, MLOps, DataOps!",
            }}
          >
            {children}
          </CopilotSidebar>
        </CopilotKit>
      </body>
    </html>
  )
}
```

**Key Features:**
- CopilotKit provider with `/api/copilotkit` runtime endpoint
- CopilotSidebar with DevOps-focused branding and messaging
- Default sidebar open for immediate AI assistance
- Geist font integration with CSS variables

### Home Page (`src/app/page.tsx`)

Currently displays a VNC interface via iframe:

```tsx
export default function Home() {
  const url = `http://localhost:6901/?password=password`

  return (
    <div className="w-full min-h-screen">
      <iframe
        src={url}
        className="w-full h-full border-0"
        title="VNC Interface"
        style={{height: '920px', width: '100%'}}
      />
    </div>
  )
}
```

**Purpose:** Provides access to the containerized development environment through a web-based VNC client.

### CopilotKit API Route (`src/app/api/copilotkit/route.ts`)

Handles the backend integration for AI capabilities. This endpoint:
- Processes CopilotKit requests
- Integrates with OpenAI or other LLM providers
- Enables the conversational AI features in the sidebar

## Development Workflow

### Package Configuration
- **Name**: `cwcd` (private package)
- **Version**: `0.1.0`
- **Scripts**: Development, build, and linting commands

### Development Commands

```bash
# Development
npm run dev          # Start development server with turbopack
npm run build        # Build production application
npm run start        # Start production server
npm run lint         # Run Next.js ESLint checks
```

### Development Server
- Uses **Turbopack** for fast development builds
- Hot reloading for React components and styles
- TypeScript error checking in real-time
- Tailwind CSS compilation and purging

## Integration Architecture

### CopilotKit Integration

The application is built around CopilotKit's conversational AI capabilities:

1. **Provider Setup**: `CopilotKit` component wraps the entire application
2. **Runtime Endpoint**: `/api/copilotkit` handles AI requests and responses  
3. **UI Component**: `CopilotSidebar` provides the chat interface
4. **Instructions**: Pre-configured with DevOps assistance context

### DevOps Assistant Configuration

The sidebar is specifically configured for DevOps assistance:
- **Title**: "Claudey With a Chance of DevOps"
- **Initial Message**: "Let's talk DevOps, MLOps, DataOps!"
- **Instructions**: General assistance with emphasis on DevOps expertise
- **Default Open**: Sidebar is immediately available upon page load

### VNC Integration

The main page currently serves as a bridge to the containerized development environment:
- **URL**: `http://localhost:6901/?password=password`
- **Purpose**: Access to Python/development containers via web browser
- **Security**: Password-protected VNC session
- **Responsive**: Full-width iframe with fixed height

## User Experience Flow

1. **Page Load**: User accesses the Next.js application
2. **CopilotKit Initialization**: AI sidebar loads with DevOps branding
3. **Development Environment**: VNC iframe provides access to containers
4. **AI Assistance**: Users can interact with the DevOps assistant via sidebar
5. **Conversational Workflow**: Natural language interaction for DevOps tasks

## Future Enhancements

### Planned Features
- Integration with Chatfield conversational forms
- Policy enforcement UI for organizational standards
- Apache Answer knowledge base integration
- Infrastructure as Code visualization
- Real-time DevOps metrics and monitoring
- Team collaboration features

### Technical Improvements
- Enhanced TypeScript configurations
- Advanced Tailwind CSS custom components  
- Performance optimizations for production
- Progressive Web App (PWA) capabilities
- Enhanced security and authentication
- Error boundary implementations

## Environment Configuration

### Development Environment
- Next.js development server on default port (3000)
- VNC server on port 6901 for container access
- CopilotKit runtime integration for AI features
- Hot reloading for rapid development

### Production Considerations
- Static export capability for deployment flexibility
- Environment variable management for API keys
- Performance monitoring and analytics integration
- CDN optimization for static assets
- Security headers and CORS configuration

## Dependencies

### Runtime Dependencies
- Next.js ecosystem (next, react, react-dom)
- CopilotKit integration packages
- Font optimization (Geist fonts)

### Development Dependencies
- TypeScript for type safety
- Tailwind CSS for styling
- PostCSS for CSS processing
- ESLint for code quality

The UI application serves as the primary web interface for CWCD, providing both direct access to development environments and AI-powered DevOps assistance through modern web technologies.