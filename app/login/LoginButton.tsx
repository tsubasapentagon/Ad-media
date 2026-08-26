export function LoginButton({ next }: { next: string }) {
  return <form action="/auth/google" method="get">
    <input type="hidden" name="next" value={next}/>
    <button type="submit" className="google-login">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285f4" d="M21.6 12.2c0-.7-.1-1.5-.2-2.2H12v4.3h5.4a4.6 4.6 0 0 1-2 3v2.8h3.3c1.9-1.8 2.9-4.4 2.9-7.9Z"/><path fill="#34a853" d="M12 22c2.7 0 5-.9 6.7-2.4l-3.3-2.8c-.9.6-2.1 1-3.4 1-2.6 0-4.8-1.8-5.6-4.1H3v2.9A10 10 0 0 0 12 22Z"/><path fill="#fbbc05" d="M6.4 13.7a6 6 0 0 1 0-3.4V7.4H3a10 10 0 0 0 0 9.2l3.4-2.9Z"/><path fill="#ea4335" d="M12 6.2c1.5 0 2.8.5 3.8 1.5l2.9-2.9A9.7 9.7 0 0 0 3 7.4l3.4 2.9C7.2 8 9.4 6.2 12 6.2Z"/></svg>
      Googleアカウントでログイン
    </button>
  </form>;
}
