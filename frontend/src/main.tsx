import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CssBaseline } from "@mui/material";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { Workspace } from "./workspace";

const queryClient = new QueryClient();
const theme = createTheme({
  palette: { primary: { main: "#173e36" }, secondary: { main: "#d35c3f" }, background: { default: "#f4f1ea", paper: "#fffdf8" } },
  typography: { fontFamily: "Georgia, 'Times New Roman', serif", body1: { fontFamily: "'Segoe UI', sans-serif" }, body2: { fontFamily: "'Segoe UI', sans-serif" }, button: { fontFamily: "'Segoe UI', sans-serif", textTransform: "none", fontWeight: 700 } },
  shape: { borderRadius: 8 },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Workspace />
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);
