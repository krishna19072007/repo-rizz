# Repo Rizz — Architecture Decisions

## D1: Next.js App Router
**Decision**: Use Next.js 16 App Router
**Reason**: Server components, streaming, API routes, best React framework
**Trade-off**: Latest APIs, some instability

## D2: Tailwind CSS
**Decision**: Tailwind v4 for styling
**Reason**: Utility-first, fast development, good with shadcn/ui
**Trade-off**: Verbose markup, learning curve

## D3: React Three Fiber for 3D
**Decision**: R3F + Drei for 3D visualization
**Reason**: React-native 3D, good ecosystem, performance
**Trade-off**: Bundle size, mobile performance concerns

## D4: Deterministic Scoring
**Decision**: All scores computed deterministically
**Reason**: Reproducible, explainable, trustworthy
**Trade-off**: Less "AI magic", more engineering

## D5: Provider Abstraction for AI
**Decision**: Abstract AI behind provider interface
**Reason**: Flexibility, vendor independence, graceful degradation
**Trade-off**: Slightly more code upfront

## D6: Demo Mode with Fixtures
**Decision**: Comprehensive demo data for offline testing
**Reason**: UX testing without API limits, showcases full product
**Trade-off**: Fixture maintenance

## D7: No Prisma for MVP
**Decision**: Direct Supabase client (when needed)
**Reason**: Simpler setup, less migration complexity
**Trade-off**: Less type safety for DB queries

## D8: Mobile-First Responsive
**Decision**: Design for mobile, enhance for desktop
**Reason**: Majority of web traffic is mobile
**Trade-off**: 3D experiences limited on mobile
