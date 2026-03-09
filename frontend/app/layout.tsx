import "./main.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import AuthProvider from "@/components/providers/AuthProvider";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import Navbar from "@/components/layout/Navbar";
import MainWrapper from "@/components/layout/MainWrapper";
const inter = Inter({ subsets: ["latin"] });
export const metadata: Metadata = {
  title: "SynthHire - AI Interview Platform",
  description: "Master your technical interviews with AI-powered practice",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ThemeProvider>
          <AuthProvider>
            <Navbar />
            <MainWrapper>{children}</MainWrapper>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
