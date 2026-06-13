import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@shared/ui/Button";
import { SwitchField } from "@shared/ui/SwitchField";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

const connectionSchema = z.object({
  token: z.string().trim().max(4096),
  remember: z.boolean(),
});

type ConnectionFormValues = z.infer<typeof connectionSchema>;

interface ConnectionCardProps {
  onSubmit: (token: string, remember: boolean) => void;
  onLogout: () => void;
  currentToken?: string;
  currentRemember?: boolean;
}

export function ConnectionCard({
  onSubmit,
  onLogout,
  currentToken = "",
  currentRemember = false,
}: ConnectionCardProps) {
  const form = useForm<ConnectionFormValues>({
    resolver: zodResolver(connectionSchema),
    defaultValues: {
      token: currentToken,
      remember: currentRemember,
    },
    values: {
      token: currentToken,
      remember: currentRemember,
    },
  });

  const tokenError = form.formState.errors.token?.message;

  const handleSubmit = form.handleSubmit((values) => {
    onSubmit(values.token, values.remember);
  });

  return (
    <form onSubmit={handleSubmit} aria-label="Connect to local Mery">
      <div className="form-field">
        <label htmlFor="connection-token">Bearer token</label>
        <input
          id="connection-token"
          type="password"
          autoComplete="off"
          aria-label="Bearer token"
          aria-invalid={Boolean(tokenError)}
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
      <Button type="submit" variant="primary">
        Use token
      </Button>
      <Button type="button" onClick={onLogout}>
        Log out
      </Button>
    </form>
  );
}
