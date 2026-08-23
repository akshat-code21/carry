import { SignIn } from "@clerk/nextjs";
import { InviteCodeCapture } from "@/components/InviteCodeCapture";

export const metadata = { title: "Sign in — Carry" };

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas">
      <InviteCodeCapture />
      <SignIn />
    </div>
  );
}
