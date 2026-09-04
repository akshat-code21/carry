import { SignUp } from "@clerk/nextjs";
import { InviteCodeCapture } from "@/components/InviteCodeCapture";

export const metadata = { title: "Sign up - Carry" };

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas">
      <InviteCodeCapture />
      <SignUp />
    </div>
  );
}
