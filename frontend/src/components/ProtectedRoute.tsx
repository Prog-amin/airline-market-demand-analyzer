import React, { useEffect, useState } from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { selectIsAuthenticated } from '../features/auth/authSlice';
import { CircularProgress, Box } from '@mui/material';

interface ProtectedRouteProps {
  children?: React.ReactNode;
  requiredRole?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const [isLoading, setIsLoading] = useState(true);
  const location = useLocation();

  // Check authentication status when the component mounts or auth state changes
  useEffect(() => {
    const checkAuth = async () => {
      // In a real app, you might want to verify the token with the server here
      setIsLoading(false);
    };

    checkAuth();
  }, [isAuthenticated]);

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page, but save the current location they were trying to go to
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If there's a required role, check if the user has it
  // You would implement this based on your user role system
  // if (requiredRole && user.role !== requiredRole) {
  //   return <Navigate to="/unauthorized" replace />;
  // }

  // If authenticated and has required role (if any), render the children or outlet
  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
