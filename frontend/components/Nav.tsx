import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/attack", label: "Attack" },
  { href: "/defend", label: "Defend" },
  { href: "/protect", label: "Protect" },
];

export default function Nav() {
  return (
    <nav className="border-b border-slate-800 bg-slate-900/60">
      <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-4">
        <Link href="/" className="font-bold text-emerald-400">🛡️ Kavach</Link>
        {links.map((l) => (
          <Link key={l.href} href={l.href} className="text-sm text-slate-300 hover:text-white">
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
