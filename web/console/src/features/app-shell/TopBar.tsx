import { Button } from "@shared/ui/Button";
import { Controller, type UseFormReturn } from "react-hook-form";
import { SwitchField } from "@shared/ui/SwitchField";
import { useNavigation } from "./NavigationContext";
import { consoleSections } from "./routes";

export interface SessionFormValues {
  token: string;
  remember: boolean;
}

interface TopBarProps {
  form: UseFormReturn<SessionFormValues>;
  onSubmit: React.FormEventHandler<HTMLFormElement>;
  onLogout: () => void;
}

const sectionTitles: Record<string, string> = {
  voices:     "Voices",
  playground: "Playground",
  health:     "Health",
  developer:  "Developer",
};

export function TopBar({ form, onSubmit, onLogout }: TopBarProps) {
  const { activeSection } = useNavigation();
  const title = sectionTitles[activeSection] ?? "Console";
  const tokenError = form.formState.errors.token?.message;

  return (
    <header className="topbar" role="banner">
      <span className="topbar-title">{title}</span>

      <form className="topbar-auth" onSubmit={onSubmit} aria-label="Session">
        <div className="topbar-token-field">
          <div className="form-field">
            <label htmlFor="topbar-token">Bearer token</label>
            <input
              id="topbar-token"
              type="password"
              autoComplete="off"
              aria-label="Bearer token"
              aria-invalid={Boolean(tokenError)}
              style={{ minWidth: 200 }}
              {...form.register("token")}
            />
            {tokenError && (
              <p className="field-error" role="alert">
                {tokenError}
              </p>
            )}
          </div>
          <Controller
            control={form.control}
            name="remember"
            render={({ field }) => (
              <SwitchField
                checked={field.value}
                label="Remember"
                onCheckedChange={field.onChange}
              />
            )}
          />
        </div>
        <Button type="submit" variant="primary">
          Use token
        </Button>
        <Button type="button" onClick={onLogout}>
          Log out
        </Button>
      </form>
    </header>
  );
}
