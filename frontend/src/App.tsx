import { Route, Routes } from "react-router-dom";

import { AdminRoute } from "@/components/AdminRoute";
import { Navbar } from "@/components/Navbar";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import AdminPage from "@/pages/Admin";
import ChatPage from "@/pages/Chat";
import CreateListingPage from "@/pages/CreateListing";
import EditListingPage from "@/pages/EditListing";
import ExchangePage from "@/pages/Exchange";
import HomePage from "@/pages/Home";
import LeaveReviewPage from "@/pages/LeaveReview";
import ListingDetailPage from "@/pages/ListingDetail";
import LoginPage from "@/pages/Login";
import ProfilePage from "@/pages/Profile";
import RegisterPage from "@/pages/Register";
import ReservationsPage from "@/pages/Reservations";

export default function App() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
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
        </Routes>
      </main>
    </div>
  );
}
