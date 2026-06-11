import * as Dialog from "@radix-ui/react-dialog";
import type { PropsWithChildren, ReactNode } from "react";
import { Button } from "./Button";

interface ConfirmDialogProps {
  children: ReactNode;
  description: string;
  onConfirm: () => void;
  title: string;
}

export function ConfirmDialog({
  children,
  description,
  onConfirm,
  title,
}: PropsWithChildren<ConfirmDialogProps>) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>{children}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          <Dialog.Title>{title}</Dialog.Title>
          <Dialog.Description>{description}</Dialog.Description>
          <div className="dialog-actions">
            <Dialog.Close asChild>
              <Button type="button">Cancel</Button>
            </Dialog.Close>
            <Dialog.Close asChild>
              <Button type="button" variant="primary" onClick={onConfirm}>
                Confirm
              </Button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
