export function Header() {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-50">
          QuantLab
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Learn options by experimenting with the math.
        </p>
      </div>
    </header>
  );
}
