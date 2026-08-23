import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  // Guard page routes only. `/api/*` is excluded on purpose: the FastAPI
  // backend enforces authentication itself via Bearer session tokens, and
  // API responses must surface JSON 401/403 rather than HTML redirects.
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
