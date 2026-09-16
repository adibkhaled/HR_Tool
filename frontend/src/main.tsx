import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CssBaseline, Typography } from "@mui/material";
import { ThemeProvider, createTheme } from "@mui/material/styles";

const queryClient = new QueryClient();
const theme = createTheme();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Typography component="h1" variant="h4">HR Talent Matching Platform</Typography>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);
