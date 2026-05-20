import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "판례비교",
  description: "자연어 사건 설명을 기반으로 기준 판례와 다른 결론의 판례를 비교합니다."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
