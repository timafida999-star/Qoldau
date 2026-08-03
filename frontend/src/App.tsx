import { Suspense, lazy } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { AdminRoute } from "@/components/AdminRoute";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Footer } from "@/components/Footer";
import { Navbar } from "@/components/Navbar";
import { ProtectedRoute } from "@/components/ProtectedRoute";

// Route-level code splitting: heavy dependencies (Leaflet on the map pages,
// jsQR on the exchange page) load only when their page is opened instead of
// riding in one bundle for every visitor.
const AdminPage = lazy(() => import("@/pages/Admin"));
const ChatPage = lazy(() => import("@/pages/Chat"));
const CreateListingPage = lazy(() => import("@/pages/CreateListing"));
const EditListingPage = lazy(() => import("@/pages/EditListing"));
const ExchangePage = lazy(() => import("@/pages/Exchange"));
const HomePage = lazy(() => import("@/pages/Home"));
const LeaveReviewPage = lazy(() => import("@/pages/LeaveReview"));
const ListingDetailPage = lazy(() => import("@/pages/ListingDetail"));
const LoginPage = lazy(() => import("@/pages/Login"));
const NotFoundPage = lazy(() => import("@/pages/NotFound"));
const ProfilePage = lazy(() => import("@/pages/Profile"));
const RegisterPage = lazy(() => import("@/pages/Register"));
const ReservationsPage = lazy(() => import("@/pages/Reservations"));

function PageLoader() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center text-muted-foreground">
      <Loader2 className="h-6 w-6 animate-spin" />
    </div>
  );
}

export default function App() {
  const { pathname } = useLocation();
  // The chat is a fixed-height screen; a footer below it would make the page
  // scroll and slide the messages under the sticky navbar.
  const hideFooter = pathname.startsWith("/chats/");

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <main className="flex-1">
        <ErrorBoundary>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/listings/:listingId" element={<ListingDetailPage />} />
              <Route
                path="/listings/new"
                element={
                  <ProtectedRoute>
                    <CreateListingPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/listings/:listingId/edit"
                element={
                  <ProtectedRoute>
                    <EditListingPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/profile/:userId" element={<ProfilePage />} />
              <Route
                path="/reservations"
                element={
                  <ProtectedRoute>
                    <ReservationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/chats/:chatId"
                element={
                  <ProtectedRoute>
                    <ChatPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/exchanges/:exchangeId"
                element={
                  <ProtectedRoute>
                    <ExchangePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reviews/new/:exchangeId"
                element={
                  <ProtectedRoute>
                    <LeaveReviewPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <AdminPage />
                  </AdminRoute>
                }
              />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </main>
      {!hideFooter && <Footer />}
    </div>
  );
}
