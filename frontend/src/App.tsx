import React, { useMemo, useState, useEffect } from "react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Label } from "./components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import { Link as LinkIcon, Play, Search, BookOpen } from "lucide-react";

// Matches the API's BookResponseDTO structure
type BookDTO = {
  id: number; // Backend uses Long but JS handles it as number
  title: string;
  author: string;
  sourceUrl?: string; // Optional URL to the book source
  imgUrl?: string; // Optional book cover image URL
};

function CoverCard({ text, imgUrl }: { text: string; imgUrl?: string }) {
  const [imageError, setImageError] = useState(false);

  // Debug logging
  console.log(
    `CoverCard for "${text}": imgUrl = "${imgUrl}", imageError = ${imageError}`
  );

  if (imgUrl && !imageError) {
    console.log(`Attempting to display image: ${imgUrl}`);
    return (
      <div
        style={{
          width: "100%",
          height: 160,
          borderRadius: 8,
          border: "1px solid rgba(255,255,255,.1)",
          overflow: "hidden",
          background: "#1a1a1a", // Dark background for loading
        }}
      >
        <img
          src={imgUrl}
          alt={text}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain", // Better fit for book covers
            background: "#1a1a1a",
          }}
          onError={() => {
            console.log(`Image failed to load: ${imgUrl}`);
            setImageError(true);
          }}
          onLoad={() => {
            console.log(`Image loaded successfully: ${imgUrl}`);
          }}
        />
      </div>
    );
  }

  // Fallback to generated cover
  return (
    <div
      style={{
        width: "100%",
        height: 160,
        borderRadius: 8,
        background: "linear-gradient(135deg, #2d2d32, #1f1f22)",
        border: "1px solid rgba(255,255,255,.1)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 38,
        fontWeight: 700,
        color: "white",
        letterSpacing: 1.5,
        textTransform: "uppercase",
        overflow: "hidden",
      }}
    >
      {text}
    </div>
  );
}

/* Helpers dynamiques titre + cover */
function extractTitle(text: string): string | null {
  const lines = text.split(/\r?\n/).slice(0, 250);
  for (const line of lines) {
    const m = line.match(/^Title:\s*(.*)$/i);
    if (m) return m[1].trim();
  }
  return null;
}

function extractGutenbergId(url: string): string | null {
  if (!url) return null;

  // cas: .../pg77012.txt
  let m = url.match(/pg(\d+)\.txt$/i);
  if (m) return m[1];

  // cas: .../77012.txt
  m = url.match(/\/(\d+)\.txt$/i);
  if (m) return m[1];

  // cas: .../1661-0.txt -> on prend 1661
  m = url.match(/\/(\d+)[-_]\d+\.txt$/i);
  if (m) return m[1];

  return null;
}

function coverUrlFromId(id: string) {
  return `https://www.gutenberg.org/cache/epub/${id}/pg${id}.cover.medium.jpg`;
}

function VscodeTopbar({ title = "DAAR - egrep clone" }) {
  return (
    <div className="topbar">
      <div className="flex" style={{ gap: 8 }}>
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: 12,
            background: "#ff5f57",
            display: "inline-block",
          }}
        />
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: 12,
            background: "#febc2e",
            display: "inline-block",
          }}
        />
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: 12,
            background: "#28c840",
            display: "inline-block",
          }}
        />
        <span
          style={{
            margin: "0 12px",
            borderLeft: "1px solid rgba(255,255,255,.1)",
            height: 16,
          }}
        />
        <div style={{ fontSize: 12, opacity: 0.8 }}>{title}</div>
      </div>
    </div>
  );
}

function highlightMatches(line: string, regex: RegExp) {
  const parts: { t: string; hl: boolean }[] = [];
  let lastIndex = 0;
  const flags = regex.flags.includes("g") ? regex.flags : regex.flags + "g";
  const re = new RegExp(regex.source, flags);
  let m: RegExpExecArray | null;
  while ((m = re.exec(line)) !== null) {
    const match = m[0] ?? "";
    const start = m.index;
    const end = start + match.length;
    if (start > lastIndex)
      parts.push({ t: line.slice(lastIndex, start), hl: false });
    parts.push({ t: line.slice(start, end), hl: true });
    lastIndex = end;
    if (match.length === 0) re.lastIndex = start + 1;
  }
  if (lastIndex < line.length)
    parts.push({ t: line.slice(lastIndex), hl: false });
  return parts;
}

function shortTitle(title: string): string {
  if (!title) return "BOOK";
  const words = title.split(/\s+/).filter(Boolean);
  if (!words.length) return "BOOK";
  if (words.length === 1) return words[0].slice(0, 8).toUpperCase();
  const firstTwo = words
    .slice(0, 2)
    .map((w) => (w[0] ?? "").toUpperCase())
    .join("");
  return firstTwo || "BOOK";
}

/* Section suggestions de livres + catalogue (depuis backend) */
function BookSuggestionsSection(props: {
  mainTitle: string | null;
  bookId: string | null;
  bookCover: string | null;
  suggestions: BookDTO[];
}) {
  const { mainTitle, bookId, bookCover, suggestions } = props;

  return (
    <div className="card section" style={{ marginTop: 24 }}>
      <div className="card-header">
        <div className="card-title">
          <span className="flex" style={{ gap: 8, alignItems: "center" }}>
            <BookOpen size={18} /> Suggestions de lecture (backend)
          </span>
        </div>
      </div>

      <div className="card-content">
        {mainTitle && (
          <div
            style={{
              display: "flex",
              gap: 16,
              alignItems: "center",
              marginBottom: 20,
            }}
          >
            {bookCover && (
              <img
                src={bookCover}
                alt={mainTitle}
                style={{
                  width: 64,
                  height: 96,
                  objectFit: "cover",
                  borderRadius: 6,
                  border: "1px solid rgba(255,255,255,.12)",
                }}
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            )}
            <div>
              <div className="book-title">{mainTitle}</div>
              {bookId && (
                <div className="lh-xs" style={{ opacity: 0.7 }}>
                  Texte analysé · Gutenberg #{bookId}
                </div>
              )}
            </div>
          </div>
        )}

        {!suggestions.length && (
          <div className="lh-xs">
            Aucune suggestion disponible pour le moment.
          </div>
        )}

        {suggestions.length > 0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
              gap: 20,
            }}
          >
            {suggestions.map((b) => {
              const isClickable = !!b.sourceUrl;
              const cardContent = (
                <>
                  <CoverCard text={shortTitle(b.title)} imgUrl={b.imgUrl} />

                  <div
                    style={{
                      fontSize: 15,
                      fontWeight: 600,
                      color: isClickable ? "#e8e8e8" : "inherit",
                      textDecoration: "none",
                      cursor: isClickable ? "pointer" : "default",
                      transition: "color 0.2s ease",
                      opacity: isClickable ? 0.9 : 1,
                    }}
                    onMouseEnter={(e) => {
                      if (isClickable) {
                        e.currentTarget.style.color = "#ffffff";
                        e.currentTarget.style.opacity = "1";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (isClickable) {
                        e.currentTarget.style.color = "#e8e8e8";
                        e.currentTarget.style.opacity = "0.9";
                      }
                    }}
                  >
                    {b.title}
                  </div>
                  <div style={{ fontSize: 13, opacity: 0.75 }}>
                    Auteur : {b.author}
                  </div>

                  <span
                    style={{
                      alignSelf: "flex-start",
                      fontSize: 12,
                      padding: "2px 8px",
                      borderRadius: 999,
                      background: "#323238",
                      opacity: 0.85,
                    }}
                  >
                    Recommandation catalogue
                  </span>
                </>
              );

              return isClickable ? (
                <a
                  key={b.id}
                  href={b.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    background: "#242428",
                    borderRadius: 10,
                    padding: 12,
                    border: "1px solid rgba(255,255,255,.06)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                    textDecoration: "none",
                    color: "inherit",
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "#2a2a30";
                    e.currentTarget.style.borderColor =
                      "rgba(74, 158, 255, 0.3)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "#242428";
                    e.currentTarget.style.borderColor = "rgba(255,255,255,.06)";
                  }}
                >
                  {cardContent}
                </a>
              ) : (
                <div
                  key={b.id}
                  style={{
                    background: "#242428",
                    borderRadius: 10,
                    padding: 12,
                    border: "1px solid rgba(255,255,255,.06)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  {cardContent}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
function BookResultsSection(props: { books: BookDTO[] }) {
  const { books } = props;

  // Debug: Log all received books with their image URLs
  console.log("BookResultsSection received books:", books);
  books.forEach((book, index) => {
    console.log(`Book ${index + 1}:`, {
      id: book.id,
      title: book.title,
      author: book.author,
      sourceUrl: book.sourceUrl,
      imgUrl: book.imgUrl,
      hasImgUrl: !!book.imgUrl,
      hasSourceUrl: !!book.sourceUrl,
    });
  });

  if (!books.length) return null;

  return (
    <div style={{ marginTop: 16 }}>
      <div className="lh-xs" style={{ marginBottom: 8 }}>
        Livres trouvés (backend) : {books.length}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
          gap: 20,
        }}
      >
        {books.map((b) => {
          const isClickable = !!b.sourceUrl;
          const cardContent = (
            <>
              <CoverCard text={shortTitle(b.title)} imgUrl={b.imgUrl} />

              <div
                style={{
                  fontSize: 15,
                  fontWeight: 600,
                  color: isClickable ? "#e8e8e8" : "inherit",
                  textDecoration: "none",
                  cursor: isClickable ? "pointer" : "default",
                  transition: "color 0.2s ease",
                  opacity: isClickable ? 0.9 : 1,
                }}
                onMouseEnter={(e) => {
                  if (isClickable) {
                    e.currentTarget.style.color = "#ffffff";
                    e.currentTarget.style.opacity = "1";
                  }
                }}
                onMouseLeave={(e) => {
                  if (isClickable) {
                    e.currentTarget.style.color = "#e8e8e8";
                    e.currentTarget.style.opacity = "0.9";
                  }
                }}
              >
                {b.title}
              </div>
              <div style={{ fontSize: 13, opacity: 0.75 }}>
                Auteur : {b.author}
              </div>

              <span
                style={{
                  alignSelf: "flex-start",
                  fontSize: 12,
                  padding: "2px 8px",
                  borderRadius: 999,
                  background: "#323238",
                  opacity: 0.85,
                }}
              >
                Résultat catalogue
              </span>
            </>
          );

          return isClickable ? (
            <a
              key={b.id}
              href={b.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                background: "#242428",
                borderRadius: 10,
                padding: 12,
                border: "1px solid rgba(255,255,255,.06)",
                display: "flex",
                flexDirection: "column",
                gap: 8,
                textDecoration: "none",
                color: "inherit",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "#2a2a30";
                e.currentTarget.style.borderColor = "rgba(74, 158, 255, 0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "#242428";
                e.currentTarget.style.borderColor = "rgba(255,255,255,.06)";
              }}
            >
              {cardContent}
            </a>
          ) : (
            <div
              key={b.id}
              style={{
                background: "#242428",
                borderRadius: 10,
                padding: 12,
                border: "1px solid rgba(255,255,255,.06)",
                display: "flex",
                flexDirection: "column",
                gap: 8,
              }}
            >
              {cardContent}
            </div>
          );
        })}
      </div>
    </div>
  );
}
export default function App() {
  const [view, setView] = useState<"search" | "results">("search");
  const [values, setValues] = useState({
    pattern: "",
    url: "",
    pasted: "",
    // "title" | "tc" | "class"
    algo: "title",
    caseSensitive: false,
    wholeLine: false,
    showStats: true,
  });

  const [sourceText, setSourceText] = useState("");
  const [error, setError] = useState("");

  /* Nouveaux states: livre dynamique */
  const [bookTitle, setBookTitle] = useState<string | null>(null);
  const [bookCover, setBookCover] = useState<string | null>(null);
  const [bookId, setBookId] = useState<string | null>(null);

  /* Affichage conditionnel des suggestions */
  const [showSuggestions, setShowSuggestions] = useState(false);

  /* Backend: résultats de recherche et suggestions */
  const [backendBooks, setBackendBooks] = useState<BookDTO[]>([]);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [loadingBackend, setLoadingBackend] = useState(false);

  const [suggestedBooks, setSuggestedBooks] = useState<BookDTO[]>([]);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  /* Track if a search has been performed (required for suggestions API) */
  const [hasSearched, setHasSearched] = useState(false);

  /* Pagination for backend results */
  const [currentPage, setCurrentPage] = useState(1);
  const [booksPerPage, setBooksPerPage] = useState(5); // Show 5 books per page

  const results = useMemo(() => {
    if (view !== "results")
      return {
        lines: [] as any[],
        stats: { total: 0, matched: 0, occurrences: 0 },
      };
    const res = {
      lines: [] as any[],
      stats: { total: 0, matched: 0, occurrences: 0 },
    };
    try {
      const flags = values.caseSensitive ? "g" : "gi";
      const user = values.wholeLine ? `^${values.pattern}$` : values.pattern;
      const re = new RegExp(user, flags);
      const arr = sourceText.split(/\r?\n/);
      res.stats.total = arr.length;
      arr.forEach((line, idx) => {
        re.lastIndex = 0;
        if (re.test(line)) {
          res.stats.matched += 1;
          const reCount = new RegExp(
            re.source,
            re.flags.includes("g") ? re.flags : re.flags + "g"
          );
          let count = 0;
          let m: RegExpExecArray | null;
          while ((m = reCount.exec(line)) !== null) {
            count++;
            if ((m[0] ?? "").length === 0) reCount.lastIndex = m.index + 1;
          }
          res.stats.occurrences += Math.max(count, 1);
          const reHL = new RegExp(
            re.source,
            re.flags.includes("g") ? re.flags : re.flags + "g"
          );
          const parts = highlightMatches(line, reHL);
          res.lines.push({ n: idx + 1, parts });
        }
      });
    } catch (e) {
      setError("Motif invalide");
    }
    return res;
  }, [view, values, sourceText]);

  const handleSend = async () => {
    setError("");
    setShowSuggestions(false);
    setBackendError(null);
    setSuggestionsError(null);
    setBackendBooks([]);
    setSuggestedBooks([]);
    setHasSearched(false); // Reset search state
    setCurrentPage(1); // Reset to first page

    const u = (values.url || "").trim();
    let txt = values.pasted || "";

    if (u.startsWith("http://") || u.startsWith("https://")) {
      try {
        const resp = await fetch(u);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        txt = await resp.text();
        setSourceText(txt);

        const title = extractTitle(txt);
        const id = extractGutenbergId(u);

        setBookTitle(title ?? "Titre non trouvé");
        setBookId(id);

        if (id) {
          setBookCover(coverUrlFromId(id));
        } else {
          setBookCover(null);
        }
      } catch (e) {
        setError("Impossible de charger l’URL. Vérifiez le lien ou les CORS.");
        setSourceText(values.pasted || "");
        setBookTitle(null);
        setBookCover(null);
        setBookId(null);
      }
    } else {
      setSourceText(txt);
      setBookTitle(txt ? "Texte collé" : null);
      setBookCover(null);
      setBookId(null);
    }

    /* Appel backend: on choisit l'endpoint selon le type de recherche */
    try {
      setLoadingBackend(true);

      let endpoint = "";
      let body: any = { pattern: values.pattern || "" };

      if (values.algo === "title") {
        endpoint = "searchByTitle";
      } else if (values.algo === "tc") {
        endpoint = "searchByTC";
        body.maxWords = 100;
        body.maxLength = 500;
      } else {
        endpoint = "classSearch";
        body.maxWords = 1000;
        body.maxLength = 5000;
      }

      const url = `/api/v1/search/${endpoint}`;
      console.log("=== FRONTEND API DEBUG ===");
      console.log("Algorithm:", values.algo);
      console.log("Pattern:", values.pattern);
      console.log("Endpoint:", endpoint);
      console.log("Request body:", JSON.stringify(body, null, 2));
      console.log("Full URL:", url);
      console.log("========================");

      const resp = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();
      if (Array.isArray(data)) {
        setBackendBooks(data as BookDTO[]);
        setHasSearched(true); // Mark that a search has been performed for suggestions
      } else {
        setBackendBooks([]);
        setHasSearched(true);
      }
    } catch (e) {
      console.error("Backend search error:", e);

      // More detailed error messages for debugging
      let errorMessage = "Erreur lors de la recherche de livres (backend).";
      if (e instanceof Error) {
        if (e.message.includes("Failed to fetch")) {
          errorMessage =
            "Impossible de se connecter au serveur backend. Vérifiez que l'API est lancée sur http://localhost:8080";
        } else if (e.message.includes("HTTP 404")) {
          errorMessage = "Endpoint non trouvé (404). Vérifiez l'URL de l'API.";
        } else if (e.message.includes("HTTP 500")) {
          errorMessage = "Erreur serveur (500). Vérifiez les logs du backend.";
        } else if (e.message.includes("HTTP 400")) {
          errorMessage =
            "Requête invalide (400). Vérifiez le format des données envoyées.";
        } else {
          errorMessage = `Erreur backend: ${e.message}`;
        }
      }

      setBackendError(errorMessage);
      setBackendBooks([]);
    } finally {
      setLoadingBackend(false);
    }

    setView("results");
  };

  const handleToggleSuggestions = async () => {
    if (showSuggestions) {
      setShowSuggestions(false);
      return;
    }

    // Per API docs: suggestions depend on the last search results
    if (!hasSearched) {
      setSuggestionsError(
        "Veuillez d'abord effectuer une recherche avant de voir les suggestions."
      );
      setShowSuggestions(true);
      return;
    }

    setSuggestionsError(null);
    setLoadingSuggestions(true);
    try {
      const resp = await fetch("/api/v1/search/suggestionSearch?top_n=10", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const data = await resp.json();
      if (Array.isArray(data)) {
        setSuggestedBooks(data as BookDTO[]);
      } else {
        setSuggestedBooks([]);
      }
      setShowSuggestions(true);
    } catch (e) {
      console.error(e);
      setSuggestionsError("Erreur lors du chargement des suggestions.");
      setSuggestedBooks([]);
      setShowSuggestions(true);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  useEffect(() => {
    try {
      const re2 = new RegExp("Sargon", "g");
      const count2 = ["sargon"].reduce(
        (acc, line) => (re2.test(line) ? acc + 1 : acc),
        0
      );
      console.assert(count2 === 0, `Test2 attendu 0, obtenu ${count2}`);

      const pattern3 = "foo";
      const re3 = new RegExp(`^${pattern3}$`, "g");
      const text3 = ["foo", "bar", "foo bar"].join("\n");
      const count3 = text3
        .split(/\r?\n/)
        .reduce((acc, line) => (re3.test(line) ? acc + 1 : acc), 0);
      console.assert(count3 === 1, `Test3 attendu 1, obtenu ${count3}`);

      let threw = false;
      try {
        new RegExp("(");
      } catch (_) {
        threw = true;
      }
      console.assert(threw, "Test4 attendu une exception pour RegExp invalide");

      const re5 = new RegExp("^", "g");
      const line5 = "abc";
      let steps5 = 0;
      let m5: RegExpExecArray | null;
      while ((m5 = re5.exec(line5)) !== null && steps5 < 10) {
        steps5++;
        if ((m5[0] ?? "").length === 0) re5.lastIndex = m5.index + 1;
      }
      console.assert(
        steps5 > 0 && steps5 <= 10,
        `Test5 securite zero-length, steps=${steps5}`
      );

      const text6 = ["a", "b"].join("\n");
      const re6 = new RegExp(".", "g");
      const count6 = text6
        .split(/\r?\n/)
        .reduce((acc, line) => (re6.test(line) ? acc + 1 : acc), 0);
      console.assert(count6 === 2, `Test6 attendu 2, obtenu ${count6}`);
    } catch (e) {
      console.error("Echec des tests UI:", e);
    }
  }, []);

  return (
    <div>
      <VscodeTopbar />
      <div className="container" style={{ padding: "40px 32px" }}>
        {view === "search" && (
          <div className="card section">
            <div className="card-header">
              <div className="card-title">
                <span className="flex" style={{ gap: 8, alignItems: "center" }}>
                  <Search size={18} /> Recherche
                </span>
              </div>
            </div>
            <div className="card-content">
              <div className="row" style={{ marginBottom: 16 }}>
                <div>
                  <Label htmlFor="pattern">Motif (RegEx ERE)</Label>
                  <Input
                    id="pattern"
                    placeholder="S(a|g|r)+on"
                    style={{ width: 360, maxWidth: "100%" }}
                    value={values.pattern}
                    onChange={(e) =>
                      setValues((v) => ({ ...v, pattern: e.target.value }))
                    }
                  />
                  <div className="lh-xs">
                    (), |, concaténation, *, ., ASCII.
                  </div>
                </div>
                <div>
                  <Label htmlFor="algo">Type de recherche</Label>
                  <Select
                    value={values.algo}
                    onValueChange={(val) =>
                      setValues((v) => ({ ...v, algo: val }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choisir…" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="title">
                        Titre uniquement (searchByTitle)
                      </SelectItem>
                      <SelectItem value="tc">
                        Titre + contenu (searchByTC)
                      </SelectItem>
                      <SelectItem value="class">
                        Classe / avancée (classSearch)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div
                className="flex"
                style={{ justifyContent: "flex-end", marginTop: 16 }}
              >
                <Button onClick={handleSend}>
                  <Play size={16} /> Rechercher
                </Button>
              </div>
            </div>
          </div>
        )}

        {view === "results" && (
          <>
            <div className="card section">
              <div className="card-header">
                <div className="card-title">Résultats</div>
              </div>
              <div className="card-content">
                {error && (
                  <div
                    style={{
                      background: "#2a1f1f",
                      border: "1px solid rgba(127,29,29,.5)",
                      padding: 8,
                      borderRadius: 8,
                    }}
                  >
                    Erreur : {error}
                  </div>
                )}

                {bookTitle && (
                  <div className="book-header">
                    {bookCover && (
                      <img
                        src={bookCover}
                        className="book-cover"
                        alt={bookTitle}
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                        }}
                      />
                    )}
                    <div>
                      <div className="book-title">{bookTitle}</div>
                      {bookId && (
                        <div className="lh-xs" style={{ opacity: 0.7 }}>
                          Gutenberg #{bookId}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="lh-xs">
                  Motif:{" "}
                  <span className="badge mono">
                    {values.pattern || "(vide)"}
                  </span>
                </div>

                <div className="scroll" style={{ marginTop: 8 }}>
                  {(() => {
                    const { lines } = results as any;
                    if (!lines.length)
                      return (
                        <div className="lh-xs" style={{ padding: "12px 16px" }}>
                          Aucune correspondance.
                        </div>
                      );
                    return (
                      <div>
                        {lines.map((L: any) => (
                          <div
                            key={L.n}
                            style={{
                              display: "flex",
                              gap: 12,
                              padding: "10px 16px",
                              borderBottom: "1px solid rgba(255,255,255,.06)",
                            }}
                          >
                            <div
                              style={{
                                width: 48,
                                textAlign: "right",
                                color: "rgba(255,255,255,.5)",
                              }}
                              className="mono"
                            >
                              {L.n}
                            </div>
                            <div className="mono" style={{ flex: 1 }}>
                              {L.parts.map((p: any, i: number) =>
                                p.hl ? (
                                  <mark key={i} className="mark">
                                    {p.t}
                                  </mark>
                                ) : (
                                  <span key={i}>{p.t}</span>
                                )
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  })()}
                </div>

                {values.showStats && (
                  <div className="lh-xs" style={{ marginTop: 10 }}>
                    Lignes totales: {(results as any).stats.total} · Lignes
                    correspondantes: {(results as any).stats.matched} ·
                    Occurrences: {(results as any).stats.occurrences}
                  </div>
                )}

                {/* Résultats catalogue backend */}
                {backendError && (
                  <div
                    style={{
                      marginTop: 12,
                      background: "#2a1f1f",
                      border: "1px solid rgba(127,29,29,.5)",
                      padding: 8,
                      borderRadius: 8,
                    }}
                  >
                    {backendError}
                  </div>
                )}

                {loadingBackend && (
                  <div className="lh-xs" style={{ marginTop: 8 }}>
                    Recherche de livres (backend) en cours...
                  </div>
                )}

                {!loadingBackend &&
                  backendBooks.length > 0 &&
                  (() => {
                    const totalPages = Math.ceil(
                      backendBooks.length / booksPerPage
                    );
                    const startIndex = (currentPage - 1) * booksPerPage;
                    const endIndex = startIndex + booksPerPage;
                    const currentBooks = backendBooks.slice(
                      startIndex,
                      endIndex
                    );

                    return (
                      <div style={{ marginTop: 12 }}>
                        {/* Books per page selector */}
                        <div
                          className="flex"
                          style={{
                            justifyContent: "space-between",
                            alignItems: "center",
                            marginBottom: 8,
                          }}
                        >
                          <div className="lh-xs">
                            Livres trouvés : {backendBooks.length} (page{" "}
                            {currentPage} sur {totalPages})
                          </div>
                          <div
                            className="flex"
                            style={{ gap: 8, alignItems: "center" }}
                          >
                            <div
                              className="flex"
                              style={{ gap: 4, alignItems: "center" }}
                            >
                              <span style={{ fontSize: 12, opacity: 0.8 }}>
                                Livres par page:
                              </span>
                              <Select
                                value={booksPerPage.toString()}
                                onValueChange={(val) => {
                                  const newPerPage = parseInt(val);
                                  setBooksPerPage(newPerPage);
                                  // Reset to page 1 when changing items per page
                                  setCurrentPage(1);
                                }}
                              >
                                <SelectTrigger
                                  style={{
                                    width: 70,
                                    height: 28,
                                    fontSize: 12,
                                  }}
                                >
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="5">5</SelectItem>
                                  <SelectItem value="10">10</SelectItem>
                                  <SelectItem value="20">20</SelectItem>
                                  <SelectItem value="50">50</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                        </div>

                        {/* Navigation controls */}
                        <div
                          className="flex"
                          style={{
                            justifyContent: "space-between",
                            alignItems: "center",
                            marginBottom: 8,
                          }}
                        >
                          <div></div>
                          <div className="flex" style={{ gap: 8 }}>
                            <Button
                              variant="secondary"
                              style={{ padding: "4px 8px", fontSize: 12 }}
                              disabled={currentPage === 1}
                              onClick={() => setCurrentPage(currentPage - 1)}
                            >
                              ← Précédent
                            </Button>
                            <Button
                              variant="secondary"
                              style={{ padding: "4px 8px", fontSize: 12 }}
                              disabled={currentPage === totalPages}
                              onClick={() => setCurrentPage(currentPage + 1)}
                            >
                              Suivant →
                            </Button>
                          </div>
                        </div>

                        <BookResultsSection books={currentBooks} />

                        {/* Page numbers for easier navigation */}
                        {totalPages > 1 && (
                          <div
                            className="flex"
                            style={{
                              justifyContent: "center",
                              marginTop: 12,
                              gap: 4,
                            }}
                          >
                            {Array.from(
                              { length: Math.min(totalPages, 10) },
                              (_, i) => {
                                const pageNum = i + 1;
                                if (
                                  totalPages <= 10 ||
                                  pageNum <= 5 ||
                                  pageNum > totalPages - 5 ||
                                  Math.abs(pageNum - currentPage) <= 2
                                ) {
                                  return (
                                    <button
                                      key={pageNum}
                                      onClick={() => setCurrentPage(pageNum)}
                                      style={{
                                        padding: "4px 8px",
                                        fontSize: 12,
                                        background:
                                          pageNum === currentPage
                                            ? "#2b6cb0"
                                            : "#374151",
                                        color: "white",
                                        border: "none",
                                        borderRadius: 4,
                                        cursor: "pointer",
                                      }}
                                    >
                                      {pageNum}
                                    </button>
                                  );
                                }
                                return null;
                              }
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })()}

                {suggestionsError && (
                  <div
                    style={{
                      marginTop: 12,
                      background: "#2a1f1f",
                      border: "1px solid rgba(127,29,29,.5)",
                      padding: 8,
                      borderRadius: 8,
                    }}
                  >
                    {suggestionsError}
                  </div>
                )}

                <div
                  className="flex"
                  style={{
                    marginTop: 14,
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setShowSuggestions(false);
                      setView("search");
                    }}
                  >
                    ← Modifier la recherche
                  </Button>

                  <Button
                    variant="secondary"
                    onClick={handleToggleSuggestions}
                    disabled={loadingSuggestions}
                  >
                    {loadingSuggestions
                      ? "Chargement..."
                      : showSuggestions
                      ? "Masquer les suggestions"
                      : "Afficher les suggestions"}
                  </Button>
                </div>
              </div>
            </div>

            {showSuggestions && (
              <BookSuggestionsSection
                mainTitle={bookTitle}
                bookId={bookId}
                bookCover={bookCover}
                suggestions={suggestedBooks}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
