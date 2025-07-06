import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Box, Button, Container, Grid, Typography, useTheme, useMediaQuery, Paper, Card, CardContent, CardActions } from '@mui/material';
import { styled } from '@mui/material/styles';
import { FlightTakeoff, BarChart, Search, TrendingUp, Security, Speed, Group } from '@mui/icons-material';
import { selectIsAuthenticated } from '../features/auth/authSlice';

const StyledHero = styled(Box)(({ theme }) => ({
  position: 'relative',
  backgroundColor: theme.palette.grey[100],
  padding: theme.spacing(8, 0, 12),
  marginBottom: theme.spacing(8),
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(156, 39, 176, 0.1) 100%)',
    zIndex: 0,
  },
}));

const FeatureCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-8px)',
    boxShadow: theme.shadows[8],
  },
}));

const FeatureIcon = styled(Box)(({ theme }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: 60,
  height: 60,
  borderRadius: '50%',
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  marginBottom: theme.spacing(2),
  '& svg': {
    fontSize: 30,
  },
}));

const features = [
  {
    icon: <Search />,
    title: 'Advanced Search',
    description: 'Find the best flight options with our powerful search engine that compares prices across multiple airlines.',
  },
  {
    icon: <BarChart />,
    title: 'Market Analytics',
    description: 'Get real-time insights into flight prices, demand trends, and booking patterns.',
  },
  {
    icon: <TrendingUp />,
    title: 'Price Predictions',
    description: 'Our AI-powered system predicts future price changes to help you book at the best time.',
  },
  {
    icon: <Security />,
    title: 'Secure Booking',
    description: 'Your transactions are protected with industry-standard encryption and security measures.',
  },
];

const HomePage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate(isAuthenticated ? '/flights' : '/register');
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Hero Section */}
      <StyledHero>
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6} sx={{ position: 'relative', zIndex: 1 }}>
              <Typography
                component="h1"
                variant={isMobile ? 'h3' : 'h2'}
                gutterBottom
                sx={{
                  fontWeight: 700,
                  lineHeight: 1.2,
                  mb: 3,
                  background: 'linear-gradient(45deg, #1976d2 30%, #9c27b0 90%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Smart Airline Market Analysis
              </Typography>
              <Typography
                variant="h6"
                color="text.secondary"
                paragraph
                sx={{ mb: 4, fontSize: isMobile ? '1.1rem' : '1.25rem' }}
              >
                Get real-time flight data, price trends, and booking insights to make informed travel decisions.
                Save money and time with our advanced analytics platform.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGetStarted}
                  sx={{
                    px: 4,
                    py: 1.5,
                    fontSize: '1.1rem',
                    textTransform: 'none',
                    borderRadius: 2,
                  }}
                >
                  {isAuthenticated ? 'Search Flights' : 'Get Started'}
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate('/about')}
                  sx={{
                    px: 4,
                    py: 1.5,
                    fontSize: '1.1rem',
                    textTransform: 'none',
                    borderRadius: 2,
                  }}
                >
                  Learn More
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={6} sx={{ position: 'relative', zIndex: 1 }}>
              <Box
                component="img"
                src="/images/hero-illustration.svg"
                alt="Airline Market Analytics"
                sx={{
                  width: '100%',
                  height: 'auto',
                  maxWidth: 600,
                  display: 'block',
                  margin: '0 auto',
                }}
              />
            </Grid>
          </Grid>
        </Container>
      </StyledHero>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Box textAlign="center" mb={8}>
          <Typography
            variant="h4"
            component="h2"
            gutterBottom
            sx={{ fontWeight: 700, mb: 2 }}
          >
            Powerful Features
          </Typography>
          <Typography
            variant="subtitle1"
            color="text.secondary"
            maxWidth="700px"
            mx="auto"
          >
            Our platform provides everything you need to analyze and book flights with confidence.
          </Typography>
        </Box>

        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <FeatureCard elevation={3}>
                <CardContent sx={{ flexGrow: 1, textAlign: 'center', p: 3 }}>
                  <Box display="flex" justifyContent="center">
                    <FeatureIcon>
                      {feature.icon}
                    </FeatureIcon>
                  </Box>
                  <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 600, mt: 1 }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
                <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
                  <Button size="small" color="primary">
                    Learn more
                  </Button>
                </CardActions>
              </FeatureCard>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box bgcolor="primary.main" color="primary.contrastText" py={10} mt={8}>
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Speed sx={{ fontSize: 60, mb: 2 }} />
          <Typography variant="h4" component="h2" gutterBottom sx={{ fontWeight: 700, mb: 2 }}>
            Ready to find your perfect flight?
          </Typography>
          <Typography variant="h6" sx={{ mb: 4, opacity: 0.9 }}>
            Join thousands of travelers who save on flights with our platform.
          </Typography>
          <Button
            variant="contained"
            color="secondary"
            size="large"
            onClick={handleGetStarted}
            sx={{
              px: 6,
              py: 1.5,
              fontSize: '1.1rem',
              textTransform: 'none',
              borderRadius: 2,
              fontWeight: 600,
              '&:hover': {
                backgroundColor: theme.palette.secondary.dark,
              },
            }}
          >
            {isAuthenticated ? 'Search Flights' : 'Get Started for Free'}
          </Button>
        </Container>
      </Box>
    </Box>
  );
};

export default HomePage;
