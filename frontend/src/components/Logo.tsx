import bookIcon from "../assets/open-book.png";

export function Logo() {
  return (
    <div className="flex items-center justify-center">
      <img
        src={bookIcon}
        alt="Codex Logo"
        className="w-full h-full object-contain max-h-16 p-2 px-4"
      />
    </div>
  );
}
