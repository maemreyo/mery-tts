interface AppLayoutProps {
  sidebar: React.ReactNode;
  topbar: React.ReactNode;
  children: React.ReactNode;
}

export function AppLayout({ sidebar, topbar, children }: AppLayoutProps) {
  return (
    <div className="app-layout">
      {sidebar}
      {topbar}
      <main className="content-area">{children}</main>
    </div>
  );
}
