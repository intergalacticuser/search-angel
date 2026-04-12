export default function PrivacyShield() {
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <svg
        className="w-4 h-4 text-angel-green"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fillRule="evenodd"
          d="M10 1a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616c.078.348.118.71.118 1.082 0 3.17-1.894 6.032-4.834 7.526a1 1 0 01-.996 0C7.562 13.625 5.668 10.763 5.668 7.593c0-.372.04-.734.118-1.082L4.553 5.895a1 1 0 01.894-1.789l1.599.8L11 3.323V2a1 1 0 01-1-1z"
          clipRule="evenodd"
        />
      </svg>
      <span className="text-angel-green font-mono">Private</span>
    </div>
  );
}
