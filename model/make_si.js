// Build the Section 4 Supporting Information document.
//
// BUILD COMMAND (from anywhere):   node "<repo>/make_si.js"
// Canonical output:                <repo>/SI_Section4_Transport_Model.docx
// Inputs:                          <repo>/data/reactions_50.csv
//                                  <repo>/data/parameters_provenance.csv
//
// Every path below is resolved from __dirname, NOT from the working directory. It used to read its
// two CSVs by bare relative name and write its .docx into the cwd, so `cd data && node ../make_si.js`
// was the only invocation that worked and it deposited the document in data/ — while the repo root
// held SI_Section4_Transport_Model_v3.docx, which this build never updated. Two SI documents existed,
// one stale, neither obviously canonical. There is now exactly one output path and the cwd cannot
// change it; the v3 file has been retired to _archive/ (see docs/ARCHIVE_MANIFEST.md).
const fs = require("fs");
const path = require("path");
const ROOT = __dirname;
const DATA = path.join(ROOT, "data");
const RX_CSV = path.join(DATA, "reactions_50.csv");
const PROV_CSV = path.join(DATA, "parameters_provenance.csv");
// SI_MODE=condensed builds the pre-review SI from THIS generator: the same elements, filtered by the
// explicit plan in data/si_condensed_plan.json. Nothing is written for the condensed build that the
// detailed build does not also print, so the two documents cannot disagree on a number.
const SI_MODE = process.env.SI_MODE === "condensed" ? "condensed" : "detailed";
const OUT_DOCX = path.join(ROOT, SI_MODE === "condensed"
  ? "SI_Section4_Transport_Model_condensed.docx" : "SI_Section4_Transport_Model.docx");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow,
  TableCell, WidthType, BorderStyle, PageOrientation, ShadingType, LevelFormat, PageBreak,
  Math: OMath, MathRun, MathFraction, MathRadical, MathSubScript, MathSuperScript, MathSum,
  MathRoundBrackets, MathSquareBrackets, MathFunction, TabStopType, TableLayoutType, ImageRun } = require("docx");

// ---------- RSC-style numbered references ----------
// REFS order == citation numbers (order of first appearance in the document; enforced by auditRefOrder()).
// Journal helper: authors, italic journal, year, bold volume (null for no-volume/DOI-only), pages/article no.
const J = (a, j, y, v, pg) => [{ t: a + ", " }, { t: j, i: true }, { t: ", " + y + ", " },
  ...(v !== null ? [{ t: String(v), b: true }, { t: ", " }] : []), { t: pg + "." }];

// The eleven class shares, read from the stratification's own artifact rather than typed. They had
// gone stale once: correcting row 11's class on 2026-10-05 moved two of them while G-STRAT passed,
// because that gate checks the paragraph's five CLAIMS and never the share list.
const STRAT = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "khl_stratification.json"), "utf8"));
const STRAT_NAME = {
  "Cyclization": "cyclization", "C-C formation": "C\u2013C formation", "C-N formation": "C\u2013N formation",
  "Functional group intraconversion": "functional-group intraconversion",
  "Other bond formation": "other bond formation", "Multicomponent coupling": "multicomponent coupling",
  "C-O formation": "C\u2013O formation", "Oxidation": "oxidation", "C-S formation": "C\u2013S formation",
  "Reduction": "reduction", "Halogenation": "halogenation",
};
function stratShares() {
  const parts = STRAT.shares.map(r => {
    const nm = STRAT_NAME[r.cls];
    if (!nm) throw new Error("no SI display name for stratification class " + r.cls);
    return nm + " " + r.set_pct.toFixed(1) + "% vs " + r.corpus_pct.toFixed(1) + "%";
  });
  return parts.slice(0, -1).join(", ") + " and " + parts[parts.length - 1];
}
// Which classes the set holds least of, and which it over- and under-samples, are READ from the stratification (chemistry
// audit pass 3: "multicomponent coupling, the sparsest" and "under-sampling of cyclization" were typed and went stale when
// three rows were reclassified). Each named set is asserted, so a reclassification that moves it fails the build.
// the bound word the S4.2 sentence prints, rounded up from the largest gap (G-STRAT derives the same word)
const STRAT_BOUND_WORD = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][Math.ceil(Math.max(...STRAT.shares.map(r => Math.abs(r.diff))))];
const stratList = (xs) => xs.length < 2 ? xs[0] : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1];
const STRAT_MINPCT = Math.min(...STRAT.shares.map(r => r.set_pct));
const STRAT_SPARSE = STRAT.shares.filter(r => r.set_pct === STRAT_MINPCT).map(r => STRAT_NAME[r.cls]);
const STRAT_SPARSE_N = Math.round(STRAT_MINPCT * STRAT.n_set / 100);
const STRAT_OVER = STRAT.shares.filter(r => r.diff >= 5).sort((x, y) => y.diff - x.diff).map(r => STRAT_NAME[r.cls]);
const STRAT_UNDER = STRAT.shares.filter(r => r.diff <= -5).sort((x, y) => x.diff - y.diff).map(r => STRAT_NAME[r.cls]);
// ---- S4.2: the oxygen-donor convention of the classification record, the rows it decides, and how the dataset draws
// those reagents (results/khl_stratification.json, data/khl_stratification.py)
const ODONOR = (() => { const L = fs.readFileSync(path.join(DATA, "reactions_50_khl_class.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV), h = L[0];
  const rows = L.slice(1).filter(r => r[h.indexOf("status")] === "current" && /adds only oxygen/.test(r[h.indexOf("rule")]));
  const by = {}; rows.forEach(r => { const c = r[h.indexOf("cls_khl")]; by[c] = (by[c] || 0) + 1; });
  if (!STRAT.drawn_as_reactant) throw new Error("khl_stratification.json lacks drawn_as_reactant; re-run data/khl_stratification.py");
  return { n: rows.length, by, drawn: STRAT.drawn_as_reactant }; })();
if (!sameSetStrat(STRAT_OVER, ["oxidation", "reduction"]) || !sameSetStrat(STRAT_UNDER, ["functional-group intraconversion", "other bond formation"]))
  throw new Error("the over- and under-sampled classes moved: " + JSON.stringify([STRAT_OVER, STRAT_UNDER]) + " -- re-read the S4.2 sentence before changing this check");
function sameSetStrat(a, b) { return a.length === b.length && a.every(x => b.includes(x)); }

const REFS = [
  { k: "bui2022",       s: J("J. C. Bui, E. W. Lees, L. M. Pant, I. V. Zenyuk, A. T. Bell and A. Z. Weber", "Chem. Rev.", 2022, 122, "11022–11084") },
  { k: "oliver2025",    s: J("Z. J. Oliver et al.", "ACS Cent. Sci.", 2025, 11, "528–538") },
  { k: "bard",          s: [{ t: "A. J. Bard and L. R. Faulkner, " }, { t: "Electrochemical Methods: Fundamentals and Applications", i: true }, { t: ", John Wiley & Sons, New York, 2nd edn, 2001." }] },
  { k: "watkins2023",   s: J("N. B. Watkins, Z. J. Schiffer, Y. Lai, C. B. Musgrave III, H. A. Atwater, W. A. Goddard III, T. Agapie, J. C. Peters and J. M. Gregoire", "ACS Energy Lett.", 2023, 8, "2185–2192") },
  { k: "mo2020",        s: J("Y. Mo, Z. Lu, G. Rughoobur, P. Patil, N. Gershenfeld, A. I. Akinwande, S. L. Buchwald and K. F. Jensen", "Science", 2020, 368, "1352–1357") },
  { k: "levich",        s: [{ t: "V. G. Levich, " }, { t: "Physicochemical Hydrodynamics", i: true }, { t: ", Prentice-Hall, Englewood Cliffs, NJ, 1962." }] },
  { k: "eisenberg",     s: J("M. Eisenberg, C. W. Tobias and C. R. Wilke", "J. Electrochem. Soc.", 1954, 101, "306–320") },
  { k: "wilke1955",     s: J("C. R. Wilke and P. Chang", "AIChE J.", 1955, 1, "264–270") },
  { k: "poling",        s: [{ t: "R. C. Reid, J. M. Prausnitz and B. E. Poling, " }, { t: "The Properties of Gases and Liquids", i: true }, { t: ", McGraw-Hill, New York, 4th edn, 1987." }] },
  { k: "crc",           s: [{ t: "CRC Handbook of Chemistry and Physics", i: true }, { t: ", ed. W. M. Haynes, CRC Press, Boca Raton, FL, 97th edn, 2016." }] },
  { k: "ruecker2024",   s: J("T. Rücker, T. Pettersen, H. Graute, B. Wittgens, T. Graßl and S. R. Waldvogel", "ACS Sustainable Chem. Eng.", 2024, 12, "11283–11296") },
  { k: "peters2019",    s: J("B. K. Peters et al.", "Science", 2019, 363, "838–845") },
  { k: "jang2022",      s: J("J. Jang, M. Rüscher, M. Winzely and C. G. Morales-Guio", "AIChE J.", 2022, 68, "e17605") },
  { k: "lehnherr2024",  s: J("D. Lehnherr and L. Chen", "Org. Process Res. Dev.", 2024, 28, "338–366") },
  { k: "kelly2026",     s: J("M. Kelly, L. Cardinale, K. V. Sackett, S. Zhang, G. L. Beutner, B. Cohen, S. S. Stahl and M. Schreier", "Org. Process Res. Dev.", 2026, 30, "1926\u20131936") },
  { k: "ferretti2025",  s: J("A. C. Ferretti, B. Cohen, L. Deng, M. Diwan, M. O. Frederick and D. Lehnherr", "Org. Process Res. Dev.", 2025, 29, "322–332") },
  { k: "yang2023nc",    s: J("D. Yang, Z. Guan, Y. Peng, S. Zhu, P. Wang, Z. Huang, H. Alhumade, D. Gu, H. Yi and A. Lei", "Nat. Commun.", 2023, 14, "1476") },
  { k: "chien2025",     s: J("P.-C. Chien, F. A. Breitschaft, H. Kelm, S. R. Waldvogel and G. Manolikakes", "ChemSusChem", 2025, 18, "e202500186") },
  { k: "mei2019",       s: J("H. Mei, J. Liu, Y. Guo and J. Han", "ACS Omega", 2019, 4, "14353–14359") },
  { k: "baizer1964",    s: J("M. M. Baizer", "J. Electrochem. Soc.", 1964, 111, "215–222") },
  { k: "us5507922",     s: [{ t: "D. Hermeling, H. Hannebaum, H. Voss and A. Weiper-Idelmann (BASF AG), US Pat., 5507922, 1996." }] },
  { k: "bottecchia2022",s: J("C. Bottecchia et al.", "Org. Process Res. Dev.", 2022, 26, "2423–2437") },
  { k: "puetter2001",   s: [{ t: "H. Pütter, in " }, { t: "Organic Electrochemistry", i: true }, { t: ", ed. H. Lund and O. Hammerich, Marcel Dekker, New York, 4th edn, 2001, ch. 31, pp. 1259–1308." }] },
  { k: "ep0011712",     s: [{ t: "D. Degner, M. Barl and H. Siegel (BASF AG), Eur. Pat. Appl., EP0011712A2, 1980." }] },
  { k: "us8629304",     s: [{ t: "F. Stecker, A. Fischer, J. Botzem, U. Griesbach and R. Pelzer (BASF SE), US Pat., 8629304, 2014." }] },
  { k: "leow2020",      s: J("W. R. Leow et al.", "Science", 2020, 368, "1228–1233") },
  { k: "kawamata2019",  s: J("Y. Kawamata et al.", "J. Am. Chem. Soc.", 2019, 141, "6392–6402") },
  { k: "liu2025",       s: J("Y. Liu, Y. Sun, Y. Deng and Y. Qiu", "Angew. Chem., Int. Ed.", 2025, 64, "e202504459") },
  { k: "shono1975",     s: J("T. Shono, H. Hamaguchi and Y. Matsumura", "J. Am. Chem. Soc.", 1975, 97, "4264–4268") },
  { k: "zhao2021",      s: J("H.-B. Zhao, J.-L. Zhuang and H.-C. Xu", "ChemSusChem", 2021, 14, "1692–1695") },
  { k: "fu2017",        s: J("N. Fu, G. S. Sauer, A. Saha, A. Loo and S. Lin", "Science", 2017, 357, "575–579") },
  { k: "malviya2023",   s: J("B. K. Malviya, C. Bottecchia, K. Stone, D. Lehnherr, F. Lévesque, C. O. Kappe and D. Cantillo", "Org. Process Res. Dev.", 2023, 27, "2183–2191") },
  { k: "morofuji2013",  s: J("T. Morofuji, A. Shimizu and J.-i. Yoshida", "J. Am. Chem. Soc.", 2013, 135, "5000–5003") },
  { k: "zhangxu2018",   s: J("S. Zhang, L. Li, M. Xue, R. Zhang, K. Xu and C. Zeng", "Org. Lett.", 2018, 20, "3443–3446") },
  { k: "cai2021",       s: J("C.-Y. Cai, Z.-J. Wu, J.-Y. Liu, M. Chen, J. Song and H.-C. Xu", "Nat. Commun.", 2021, 12, "3745") },
  { k: "zhangye2022",   s: J("L. Zhang, Y. Fu, Y. Shen, C. Liu, M. Sun, R. Cheng, W. Zhu, X. Qian, Y. Ma and J. Ye", "Nat. Commun.", 2022, 13, "4138") },
  { k: "gnaim2022",     s: J("S. Gnaim et al.", "Nature", 2022, 605, "687–695") },
  { k: "hioki2023",     s: J("Y. Hioki, M. Costantini, J. Griffin, K. C. Harper, M. Prado Merini, B. Nissl, Y. Kawamata and P. S. Baran", "Science", 2023, 380, "81–87") },
  { k: "zhangbaran2022",s: J("B. Zhang, Y. Gao, Y. Hioki, M. S. Oderinde, J. X. Qiao, K. X. Rodriguez, H.-J. Zhang, Y. Kawamata and P. S. Baran", "Nature", 2022, 606, "313–318") },
  { k: "kirste2012",    s: J("A. Kirste, B. Elsler, G. Schnakenburg and S. R. Waldvogel", "J. Am. Chem. Soc.", 2012, 134, "3571–3576") },
  { k: "liwilden2020",  s: J("D. Li, T.-K. Ma, R. J. Scott and J. D. Wilden", "Chem. Sci.", 2020, 11, "5333–5338") },
  { k: "qiu2018",       s: J("Y. Qiu, W.-J. Kong, J. Struwe, N. Sauermann, T. Rogge, A. Scheremetjew and L. Ackermann", "Angew. Chem., Int. Ed.", 2018, 57, "5828–5832") },
  { k: "cai2022",       s: J("C.-Y. Cai, X.-L. Lai, Y. Wang, H.-H. Hu, J. Song, Y. Yang, C. Wang and H.-C. Xu", "Nat. Catal.", 2022, 5, "943–951") },
  { k: "courtois1997",  s: J("V. Courtois, R. Barhdadi, M. Troupel and J. Périchon", "Tetrahedron", 1997, 53, "11569–11576") },
  { k: "osa1994",       s: J("T. Osa, Y. Kashiwagi, Y. Yanagisawa and J. M. Bobbitt", "J. Chem. Soc., Chem. Commun.", 1994, null, "2535–2537") },
  { k: "kisukuri2024",  s: J("C. M. Kisukuri, J. Seidler, T. Gärtner, D. F. Rohrmann and S. R. Waldvogel", "Org. Process Res. Dev.", 2024, 28, "1474–1485") },
  { k: "hayashi2022",   s: J("K. Hayashi, J. Griffin, K. C. Harper, Y. Kawamata and P. S. Baran", "J. Am. Chem. Soc.", 2022, 144, "5762–5768") },
  { k: "ke2019",        s: J("J. Ke, H. Wang, L. Zhou, C. Mou, J. Zhang, L. Pan and Y. R. Chi", "Chem. – Eur. J.", 2019, 25, "6911–6914") },
  { k: "lopezruiz2018", s: J("J. A. Lopez-Ruiz, U. Sanyal, J. Egbert, O. Y. Gutiérrez and J. Holladay", "ACS Sustainable Chem. Eng.", 2018, 6, "16073–16085") },
  { k: "zhong2021",     s: J("X. Zhong, M. A. Hoque, M. D. Graaf, K. C. Harper, F. Wang, J. D. Genders and S. S. Stahl", "Org. Process Res. Dev.", 2021, 25, "2601–2607") },
  { k: "horn2016",      s: J("E. J. Horn, B. R. Rosen, Y. Chen, J. Tang, K. Chen, M. D. Eastgate and P. S. Baran", "Nature", 2016, 533, "77–81") },
  { k: "cardiel2019",   s: J("A. C. Cardiel, B. J. Taitt and K.-S. Choi", "ACS Sustainable Chem. Eng.", 2019, 7, "11138–11149") },
  { k: "okada2016",     s: J("Y. Okada, Y. Yamaguchi, A. Ozaki and K. Chiba", "Chem. Sci.", 2016, 7, "6387–6393") },
  { k: "miller1992",    s: J("D. G. Miller and D. D. M. Wayner", "Can. J. Chem.", 1992, 70, "2485–2490") },
  { k: "walecka2022",   s: J("A. Walęcka-Kurczyk, J. Adamek, K. Walczak, M. Michalak and A. Październiok-Holewa", "RSC Adv.", 2022, 12, "2107–2114") },
  { k: "bao2022",       s: J("L. Bao, C. Liu, W. Li, J. Yu, M. Wang and Y. Zhang", "Org. Lett.", 2022, 24, "5762–5766") },
  { k: "ozaki1994",     s: J("S. Ozaki, I. Horiguchi, H. Matsushita and H. Ohmori", "Tetrahedron Lett.", 1994, 35, "725–728") },
  { k: "zhangzeng2018", s: J("S. Zhang, L. Li, H. Wang, Q. Li, W. Liu, K. Xu and C. Zeng", "Org. Lett.", 2018, 20, "252–255") },
  { k: "tajima2002",    s: J("T. Tajima, H. Ishii and T. Fuchigami", "Electrochem. Commun.", 2002, 4, "589–592") },
  { k: "zhangqiu2025",  s: J("B. Zhang et al.", "Nat. Commun.", 2025, 16, "3052") },
  { k: "gitkis2010",    s: J("A. Gitkis and J. Y. Becker", "Electrochim. Acta", 2010, 55, "5854–5859") },
  { k: "long2021",      s: J("H. Long, C. Huang, Y.-T. Zheng, Z.-Y. Li, L.-H. Jie, J. Song, S. Zhu and H.-C. Xu", "Nat. Commun.", 2021, 12, "6629") },
  { k: "gieshoff2016",  s: J("T. Gieshoff, D. Schollmeyer and S. R. Waldvogel", "Angew. Chem., Int. Ed.", 2016, 55, "9437–9440") },
  { k: "newman",        s: [{ t: "J. Newman and K. E. Thomas-Alyea, " }, { t: "Electrochemical Systems", i: true }, { t: ", John Wiley & Sons, Hoboken, NJ, 3rd edn, 2004." }] },
  { k: "saveant",       s: [{ t: "J.-M. Savéant, " }, { t: "Elements of Molecular and Biomolecular Electrochemistry: An Electrochemical Approach to Electron Transfer Chemistry", i: true }, { t: ", John Wiley & Sons, Hoboken, NJ, 2006." }] },
  { k: "wallis1946",    s: J("E. S. Wallis and J. F. Lane", "Org. React.", 1946, 3, "267–306") },
  { k: "heeb2014",      s: J("M. B. Heeb, J. Criquet, S. G. Zimmermann-Steffens and U. von Gunten", "Water Res.", 2014, 48, "15–42") },
  { k: "rafiee2018",    s: J("M. Rafiee, Z. M. Konz, M. D. Graaf, H. F. Koolman and S. S. Stahl", "ACS Catal.", 2018, 8, "6738–6744") },
  { k: "bailey2007",    s: J("W. F. Bailey, J. M. Bobbitt and K. B. Wiberg", "J. Org. Chem.", 2007, 72, "4504–4509") },
  { k: "livongunten2020", s: J("J. Li, J. Jiang, T. Manasfi and U. von Gunten", "Water Res.", 2020, 187, "116424") },
  { k: "lau2019",       s: J("S. S. Lau, K. P. Reber and A. L. Roberts", "Environ. Sci. Technol.", 2019, 53, "11133–11141") },
  { k: "ueda1987",      s: J("C. Ueda, M. Noyama, H. Ohmori and M. Masui", "Chem. Pharm. Bull.", 1987, 35, "1372–1377") },
  { k: "nutting2018",   s: J("J. E. Nutting, M. Rafiee and S. S. Stahl", "Chem. Rev.", 2018, 118, "4834–4885") },
  { k: "yang2023",      s: J("C. Yang, S. Arora, S. Maldonado, D. A. Pratt and C. R. J. Stephenson", "Nat. Rev. Chem.", 2023, 7, "653–666") },
  { k: "vo2024",        s: J("N. T. Vo, Q. Cacciuttolo, D. Pasquier and K. Larmier", "ChemElectroChem", 2024, 11, "e202400116") },
  { k: "grennberg1993", s: J("H. Grennberg, A. Gogoll and J.-E. Bäckvall", "Organometallics", 1993, 12, "1790–1793") },
  { k: "sivey2015",     s: J("J. D. Sivey, M. A. Bickley and D. A. Victor", "Environ. Sci. Technol.", 2015, 49, "4937–4945") },
  { k: "nagy2007",      s: J("P. Nagy, K. Lemma and M. T. Ashby", "Inorg. Chem.", 2007, 46, "285–292") },
  { k: "ting2022",      s: J("S. I. Ting, W. L. Williams and A. G. Doyle", "J. Am. Chem. Soc.", 2022, 144, "5575–5582") },
  { k: "till2021",      s: J("N. A. Till, S. Oh, D. W. C. MacMillan and M. J. Bird", "J. Am. Chem. Soc.", 2021, 143, "9332–9337") },
  { k: "boucher2023",   s: J("D. G. Boucher, A. D. Pendergast, X. Wu, Z. A. Nguyen, R. G. Jadhav, S. Lin, H. S. White and S. D. Minteer", "J. Am. Chem. Soc.", 2023, 145, "17665–17677") },
  { k: "wilson2024",    s: J("C. V. Wilson and P. L. Holland", "J. Am. Chem. Soc.", 2024, 146, "2685–2700") },
  { k: "lobaccaro2016", s: J("P. Lobaccaro, M. R. Singh, E. L. Clark, Y. Kwon, A. T. Bell and J. W. Ager", "Phys. Chem. Chem. Phys.", 2016, 18, "26777–26785") },

  { k: "gorski2025",    s: J("B. Górski et al.", "Nature", 2025, 637, "354–361") },
];
const RN = {};
if (process.env.SI_REFORDER) JSON.parse(fs.readFileSync(process.env.SI_REFORDER, "utf8")).forEach((k, i) => { RN[k] = i + 1; });
else REFS.forEach((r, i) => { RN[r.k] = i + 1; });
const REFKNOWN = new Set(REFS.map(r => r.k));
const SEEN = [];
// In the condensed second pass a detailed-only element still resolves its markers while it is built; it gets "?" and is never placed.
const refNum = (k) => { if (!REFKNOWN.has(k)) throw new Error("Unknown reference key: " + k); SEEN.push(k); return k in RN ? String(RN[k]) : "?"; };
// In-text markers: «key» or «k1,k2» -> superscript number(s); ⟦key⟧ or ⟦k1,k2⟧ -> plain number(s) (for table cells).
function runsFromText(text, size, base = {}) {
  // **bold** is honoured rather than printed. Ten literal ** markers were shipping in the SI --
  // markdown emphasis that nothing rendered, so a reader saw the asterisks. Split on the pairs
  // first, then run the citation scanner over each piece so a citation inside a bold span still
  // resolves. An unpaired ** is left alone rather than silently eating the rest of a paragraph.
  if (text.includes("**")) {
    const parts = text.split("**");
    if (parts.length % 2 === 1) {                       // balanced: odd indices are the bold ones
      const out = [];
      parts.forEach((piece, k) => {
        if (piece === "") return;
        out.push(...runsFromText(piece, size, { ...base, bold: k % 2 === 1 || !!base.bold }));
      });
      return out;
    }
  }
  const runs = []; const re = /«([^»]+)»|⟦([^⟧]+)⟧/g; let last = 0, m;
  const plain = (t) => { for (const piece of subSplit(t)) runs.push(new TextRun({ text: piece.t, size, font: "Calibri", ...base, subScript: piece.sub || undefined })); };
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) plain(text.slice(last, m.index));
    const nums = (m[1] || m[2]).split(",").map(s => refNum(s.trim())).join(",");
    runs.push(new TextRun({ text: nums, size, font: "Calibri", ...base, superScript: !!m[1] }));
    last = re.lastIndex;
  }
  if (last < text.length) plain(text.slice(last));
  return runs;
}
// ---- subscripts (2026-09-11, author: "stuff like i_lim or k_c ... needs to look professional"): prose written as BASE_TOKEN is
// rendered with TOKEN as a subscript run when TOKEN is the longest entry of data/subscript_tokens.json that starts the
// alphanumeric run after the underscore and either exhausts it or is followed by another symbol's underscore (nFD_SC_S).
// data/docx_text.py reads a subscript run back as "_" + text, so every gate phrase keeps its underscore spelling; the Python
// twin is data/subscripts.py. Anything else (H_EXT, si_001) stays a literal underscore and is listed at the end of the build.
const SUBTOK = JSON.parse(fs.readFileSync(path.join(__dirname, "data", "subscript_tokens.json"), "utf8")).tokens.slice().sort((a, b) => b.length - a.length);
const SUB_RE = /(?<=[A-Za-z0-9)\u0370-\u03FF\u00B5])_([A-Za-z0-9]+)/g;
const SUB_STATS = { converted: 0, literal: new Map() };
function subSplit(text) {
  const out = []; let pos = 0; let m; SUB_RE.lastIndex = 0;
  while ((m = SUB_RE.exec(text)) !== null) {
    const run = m[1]; const after = text[m.index + 1 + run.length];
    // a file name ("aan6206_fu_sm.pdf", "je3c00691_si") is literal text, never a symbol with a subscript
    const w0 = text.lastIndexOf(" ", m.index) + 1, w1e = text.indexOf(" ", m.index);
    const word = text.slice(w0, w1e < 0 ? text.length : w1e);
    if (/\.(pdf|txt|csv|json|docx|jl|py)\b|_s[im](_|\b)/.test(word)) { SUB_STATS.literal.set(m[0], (SUB_STATS.literal.get(m[0]) || 0) + 1); continue; }
    const tok = SUBTOK.find(t => run.startsWith(t) && (run.length === t.length || after === "_"));
    if (!tok) { SUB_STATS.literal.set(m[0], (SUB_STATS.literal.get(m[0]) || 0) + 1); continue; }
    if (m.index > pos) out.push({ t: text.slice(pos, m.index), sub: false });
    out.push({ t: tok, sub: true }); SUB_STATS.converted += 1;
    pos = m.index + 1 + tok.length; SUB_RE.lastIndex = pos;
  }
  if (pos < text.length) out.push({ t: text.slice(pos), sub: false });
  return out;
}
function auditRefOrder() {
  const firstSeen = []; const seenSet = new Set();
  for (const k of SEEN) if (!seenSet.has(k)) { seenSet.add(k); firstSeen.push(k); }
  const unused = REFS.map(r => r.k).filter(k => !seenSet.has(k));
  if (unused.length) throw new Error("References never cited: " + unused.join(", "));
  const expected = REFS.map(r => r.k);
  for (let i = 0; i < firstSeen.length; i++)
    if (firstSeen[i] !== expected[i])
      throw new Error("Citation-order mismatch at #" + (i + 1) + ": document first-appearance '" + firstSeen[i] +
        "' but REFS order says '" + expected[i] + "'.\nActual first-appearance order:\n" + firstSeen.join(", "));
  console.log("citation audit: " + REFS.length + " references, " + SEEN.length + " citation sites, first-appearance order OK");
  console.log("subscripts: " + SUB_STATS.converted + " rendered; left literal: " + (SUB_STATS.literal.size ? Array.from(SUB_STATS.literal.entries()).map(function (e) { return e[0] + "(" + e[1] + ")"; }).join(", ") : "none"));
}

// ---------- helpers ----------
const tagEl = (el, kind, t, lvl) => { el.__kind = kind; el.__t = String(t); if (lvl) el.__lvl = lvl; return el; };
const p = (text, opts = {}) => tagEl(new Paragraph({
  children: runsFromText(text, 20, { italics: opts.i || false, bold: opts.b || false }),
  spacing: { after: 120 }, alignment: AlignmentType.JUSTIFIED, ...opts.par }), "p", text);
// ---------- native OMML equation helpers (journal-style: centered, number flush right) ----------
const mr   = (t) => new MathRun(t);
const msub = (b, sc) => new MathSubScript({ children: [typeof b === "string" ? mr(b) : b], subScript: [mr(sc)] });
const msup = (b, sc) => new MathSuperScript({ children: [typeof b === "string" ? mr(b) : b], superScript: [mr(sc)] });
const mfr  = (n, d) => new MathFraction({ numerator: n, denominator: d });
const msq  = (c) => new MathRadical({ children: c });
const mrb  = (c) => new MathRoundBrackets({ children: c });
const msb  = (c) => new MathSquareBrackets({ children: c });
const msum = (c, sc) => new MathSum({ children: c, subScript: [mr(sc)] });
const mfun = (nm, arg) => new MathFunction({ name: [mr(nm)], children: [arg] });
const EQW = 9720;
const eqn = (segs, tag, unit) => {
  const kids = [new TextRun({ text: "\t" })];
  for (const s of segs) kids.push(s.m ? new OMath({ children: s.m })
    : new TextRun({ text: s.t, size: 19, font: "Calibri", italics: true }));
  if (unit) kids.push(new TextRun({ text: "   " + unit, size: 18, font: "Calibri" }));
  kids.push(new TextRun({ text: "\t(" + tag + ")", size: 20, font: "Calibri" }));
  return tagEl(new Paragraph({
    tabStops: [{ type: TabStopType.CENTER, position: Math.round(EQW / 2) }, { type: TabStopType.RIGHT, position: EQW }],
    spacing: { before: 100, after: 160 }, children: kids }), "eq", "(" + tag + ")");
};
const h1 = (t) => tagEl(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, size: 26, bold: true })], spacing: { before: 280, after: 140 } }), "h", t, 1);
const h2 = (t) => tagEl(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, size: 22, bold: true })], spacing: { before: 200, after: 100 } }), "h", t, 2);
const cap = (t) => tagEl(new Paragraph({ children: runsFromText(t, 18, { italics: true }), spacing: { before: 80, after: 160 } }), "cap", t);

function mkTable(headers, rows, colw, budget = 9720) {
  // Rescale the column-width ratios to EXACTLY fill the section's printable width,
  // and force fixed layout so no table can overflow the page.
  const raw = colw.reduce((a, b) => a + b, 0);
  const w = colw.map(x => Math.floor(x * budget / raw));
  w[w.length - 1] += budget - w.reduce((a, b) => a + b, 0);
  const cell = (t, bold, wd, shade) => new TableCell({
    width: { size: wd, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: "DCE6F1" } : undefined,
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({ children: runsFromText(String(t), 15, { bold: !!bold }) })] });
  return Object.assign(tagEl(new Table({
    width: { size: budget, type: WidthType.DXA }, columnWidths: w, layout: TableLayoutType.FIXED,
    rows: [new TableRow({ children: headers.map((h, i) => cell(h, true, w[i], true)), tableHeader: true }),
           ...rows.map(r => new TableRow({ children: r.map((v, i) => cell(v, false, w[i])) }))] }),
    "table", headers.join(" | ")), { __cells: rows.map(r => r.map(String).join(" | ")).join("\n") });
}

// ---------- load the 50-reaction table ----------
const csv = fs.readFileSync(RX_CSV, "utf8").trim().split("\n");
function splitCSV(line) {
  const out = []; let cur = "", q = false;
  for (const ch of line) {
    if (ch === '"') q = !q;
    else if (ch === "," && !q) { out.push(cur); cur = ""; }
    else cur += ch;
  }
  out.push(cur); return out;
}
const hdr = splitCSV(csv[0]);
const col = (name) => hdr.indexOf(name);
// The carrier CHARGE is the switch on the migration term and was not printed anywhere in this
// document until 2026-09-05, though it moves ceilings by up to 2x (the anodic decarboxylative
// ruling moved one row 65 %). It comes from data/carrier_charge.csv, the file the NP solver reads
// (run_all50_np.jl), joined by reaction name; G-NAMES asserts the two tables key on the same 50.
const CC_LINES = fs.readFileSync(path.join(DATA, "carrier_charge.csv"), "utf8").trim().split("\n").filter(l => !l.startsWith("#"));
const cchdr = splitCSV(CC_LINES[0]);
const CC = new Map(CC_LINES.slice(1).map(splitCSV).map(r => [r[cchdr.indexOf("reaction")], {
  z: r[cchdr.indexOf("z_carrier")], confidence: r[cchdr.indexOf("confidence")],
  species: r[cchdr.indexOf("carrier_species")], basis: r[cchdr.indexOf("basis")] }]));
const zOf = (rxn) => { const c = CC.get(rxn); if (!c) throw new Error("Table S2: no carrier charge for " + rxn); return c.z + (c.confidence === "high" ? "" : "*"); };
const CC_MEDIUM = [...CC.entries()].filter(([, c]) => c.confidence !== "high").map(([k]) => k);
// The reaction table records how each concentration was checked with an internal label; the printed cell states it in words.
const concProv = (t) => t.replace(/^Declared rather than exemplar-verified\./, "Declared rather than read from the exemplar.")
  .replace(/^Exemplar-verified against /, "Checked against ").replace(/^Exemplar-verified/, "Read from the exemplar");
const rxRows = csv.slice(1).map(splitCSV).map((r, k) => [
  k + 1, r[col("cls")], r[col("reaction")], r[col("carrier_type")], r[col("carrier_species")], zOf(r[col("reaction")]),
  Number(r[col("D_cm2s")]).toExponential(2), r[col("C_carrier_M")], r[col("n_carrier")],
  r[col("solvent")], r[col("electrolyte")], r[col("D_provenance")], concProv(r[col("conc_provenance")])]);

// How many rows each carrier class holds, counted from the reaction table. "the eight mediated rows"
// and "the eleven catalyst rows" were typed in a dozen places until the 2026-10-05 audit re-typed
// five rows; every such count below is one of these three.
const N_MED = rxRows.filter(r => r[3] === "mediator").length;
const N_CAT = rxRows.filter(r => r[3] === "catalyst").length;
const N_DIR = rxRows.filter(r => r[3] === "substrate").length;
if (N_MED + N_CAT + N_DIR !== rxRows.length) throw new Error("carrier types do not partition the reaction table");
// Rows whose diffusivity is a Stokes-Einstein estimate (the metal complexes, for which Le Bas has no increment).
const N_SE = rxRows.filter(r => /^Stokes-Einstein/.test(r[11])).length;
if (N_SE < 1 || N_SE > N_CAT) throw new Error("Stokes-Einstein rows: " + N_SE + " of " + N_CAT + " catalyst rows");

// ---------- Table S11: the system each rate constant was measured on, against the system its row solves ----------
// data/rate_constant_basis.csv is the one record of it (2026-10-05). data/check_rate_constant_basis.py (G-KBASIS) binds its
// k column to the solvers and reads this table back out of the built document; Table S6's k column is printed from it too,
// where it used to be typed beside an x_k that came from the matrix.
const KB = fs.readFileSync(path.join(DATA, "rate_constant_basis.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);
const kbc = (n) => { const i = KB[0].indexOf(n); if (i < 0) throw new Error("rate_constant_basis.csv has no column " + n); return i; };
const KBR = KB.slice(1);
const kbRow = (rxn) => { const r = KBR.find(x => x[kbc("reaction")] === rxn); if (!r) throw new Error("rate_constant_basis.csv has no row " + rxn); return r; };
const supDigits = (n) => String(n).replace(/-/g, "⁻").replace(/\d/g, c => "⁰¹²³⁴⁵⁶⁷⁸⁹"[+c]);
// a rate constant as the SI prints it: a decade as a power of ten, anything else to three significant figures (a measured
// value keeps its digits: 20.2 for the cyclohexene constant, 2.28 × 10⁴ for the anisole one)
const kSI = (k) => {
  const e = Math.log10(k);
  if (k >= 100 && Math.abs(e - Math.round(e)) < 1e-9) return "10" + supDigits(Math.round(e));
  if (k >= 100) { const ee = Math.floor(e); return String(Number((k / Math.pow(10, ee)).toPrecision(3))) + " × 10" + supDigits(ee); }
  return String(Number(k.toPrecision(3)));
};
const kOf = (rxn) => Number(kbRow(rxn)[kbc("k_M1s1")]);
const KCELLS = fs.readFileSync(path.join(__dirname, "results", "rate_constant_cells.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV).slice(1);
// best-of-seven ceiling of a mediated row at its adopted k and a tenfold change either way (the sweep of S5.5)
const kcBest = (rxn, tag) => { const v = KCELLS.filter(r => r[0] === rxn && r[1] === tag).map(r => Number(r[4]));
  if (v.length !== 7) throw new Error("rate_constant_cells.csv holds " + v.length + " cells for " + rxn + " / " + tag); return Math.max(...v); };
// ---------- Table S10: the balanced reaction behind every row ----------
// data/reaction_stoichiometry.csv is written by data/build_reaction_stoichiometry.py, which asserts
// atom and charge balance for every row and that its electron counts are the reaction table's.
const STO = fs.readFileSync(path.join(DATA, "reaction_stoichiometry.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);   // csv.DictWriter writes CRLF
const stoc = (n) => { const i = STO[0].indexOf(n); if (i < 0) throw new Error("reaction_stoichiometry.csv has no column " + n); return i; };
const STOR = STO.slice(1);
if (STOR.length !== rxRows.length || STOR.some((r, i) => r[stoc("reaction")] !== rxRows[i][2]))
  throw new Error("reaction_stoichiometry.csv and reactions_50.csv do not list the same rows in the same order");
const S10_KIND = { "stoichiometric": "", "ex-cell": "", "paired": " (paired cycle)", "charge-consuming": " (cycle charge)", "chain": " (chain)" };
const s10Rows = STOR.map(r => [r[stoc("row")], r[stoc("reaction")], r[stoc("electrode")], r[stoc("electroactive")],
  r[stoc("electrode_step")] + (r[stoc("solution_step")] ? ". Then: " + r[stoc("solution_step")] : ""),
  r[stoc("overall")] + (r[stoc("note")] ? " [" + r[stoc("note")] + "]" : ""),
  r[stoc("n_substrate")] + S10_KIND[r[stoc("kind")]], r[stoc("ceiling_set_by")]]);
const S10_NEUTRAL = STOR.filter(r => r[stoc("kind")] === "paired" || r[stoc("kind")] === "charge-consuming").length;
const S10_PAIRED = STOR.filter(r => r[stoc("kind")] === "paired").length;
const S10_CHAIN = STOR.filter(r => r[stoc("kind")] === "chain").length;
const S10_REAGENT = STOR.filter(r => r[stoc("electroactive")].startsWith("reagent")).length;

// ---------- load the provenance registry ----------
// Loaded HERE, before any prose, because several sentences in §S4, §S8 and §S9 quote counts out of
// it. Those counts used to be typed into the prose by hand, and every upstream reclassification
// silently falsified them: the 2026-08 kappa pass moved nine conductivities from assumption to
// derived and instantly made the §S8 census (64/79/125) wrong without touching a line of this file.
// Nothing below hardcodes a census any more — census() reads the CSV the tables are printed from,
// so the prose and Table S7 cannot disagree by construction.
// Tables S3 and S4 used to carry hand-typed numbers. That is the drift this project exists to
// prevent, and it had already happened: after HFIP's viscosity was page-anchored to Krumgalz
// Table 3 p. 578 the registry read 1.619 mPa s while Table S3 still printed the unsourced 1.650,
// so the SI contradicted its own appendix. Worse, `1 M NaOH aq` -- one of the four conductivities
// carrying a §S6 verdict -- was shown in Table S4 with a provenance state that came from a
// typed literal rather than from the registry, because it had no registry row at all.
// Both tables now take every numeric and state column from the CSVs at build time. Only the
// prose columns (Source, Margin, Note) remain authored, and they assert nothing numeric.
const SOLV_CSV = fs.readFileSync(path.join(__dirname, "data", "solvents.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n").slice(1).map(splitCSV);
const SOLV = new Map(SOLV_CSV.map(r => [r[0], { M: r[1], mu: r[2], rho: r[3], phi: r[4] }]));
// Peters et al. SM pp. S15/S17 print "LiBr (83.4 g, 1.0 mol)" and "THF (320 mL)"; moles from the printed masses,
// THF density and molar mass from solvents.csv, LiBr molar mass from the atomic masses.
const PET = (() => { const t = SOLV.get("THF"); const libr = 83.4 / (6.941 + 79.904);
  const thf = 320 * parseFloat(t.rho) / parseFloat(t.M); const ratio = thf / libr;
  if (!(ratio > 4 && ratio < 4.2)) throw new Error("Peters THF per Li moved: " + ratio);
  return { libr, thf, ratio, bound4: Math.round(100 * 4 * libr / thf), free3: Math.round(100 * (1 - 3 * libr / thf)) }; })();
// chemistry audit pass 7: the DMF attenuation read from Dorn's NaI/methanol isotherm (Table SI 97) at the molality 0.2 M
// corresponds to (apparent molar volume of NaI 0-35 cm3 mol-1); data/build_param_tables.py derives the same and asserts the
// carried conductivity
const NAI = (() => {
  const L = fs.readFileSync(path.join(__dirname, "data", "dorn_isotherms.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);
  const h = L[0]; const pts = L.slice(1).filter(r => r[h.indexOf("system")] === "NaI/MeOH")
    .map(r => [Number(r[h.indexOf("m_mol_kg")]), Number(r[h.indexOf("kappa_mScm")])]).sort((a, b) => a[0] - b[0]);
  const rho0 = Number(SOLV.get("MeOH").rho), c = 0.2, L0 = 45.23 + 62.63;
  const at = (vphi) => { const m = c / (rho0 * (1 - c * vphi)); const lo = pts.filter(p => p[0] <= m).pop(), hi = pts.find(p => p[0] >= m);
    const k = lo[1] + (hi[1] - lo[1]) * (m - lo[0]) / (hi[0] - lo[0]); return [m, k / c / L0]; };
  const [m0, r0] = at(0), [m1, r1] = at(0.035), r = 0.5 * (r0 + r1);
  return { m: m0.toFixed(3) + "–" + m1.toFixed(3), rr: r0.toFixed(3) + "–" + r1.toFixed(3), r: r.toFixed(3), k: (0.2 * 81.35 * r).toFixed(2) };
})();
const ELEC_CSV = fs.readFileSync(path.join(__dirname, "data", "electrolytes.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n").slice(1).map(splitCSV);
const ELEC = new Map(ELEC_CSV.map(r => [r[0], { kappa: r[1], state: r[2], status: r[3] }]));
// SI display names carry a volume ratio the CSV key does not ("MeCN/H2O 9:1 v/v" -> "MeCN/H2O").
function solvRow(name) {
  if (SOLV.has(name)) return SOLV.get(name);
  const base = name.split(" ")[0];
  if (SOLV.has(base)) return SOLV.get(base);
  throw new Error("Table S3 names a solvent absent from solvents.csv: " + name);
}
function elecRow(name) {
  const norm = name.replace(/ \/ /g, "/").replace(/ \(aq\)/, " aq");
  if (ELEC.has(norm)) return ELEC.get(norm);
  throw new Error("Table S4 names an electrolyte absent from electrolytes.csv: " + name);
}
// Rewrite the numeric columns of a typed row from the CSV, reporting anything that had drifted.
const TABLE_DRIFT = [];
function fromCSV(row, cols, lookup, label) {
  const src = lookup(row[0]);
  const out = row.slice();
  cols.forEach(([i, k]) => {
    const v = String(src[k]);
    const typed = String(out[i]).trim();
    // The CSV is authoritative for the VALUE; the typed string keeps the display precision, but
    // only while the two agree numerically. "0.890" against a registry 0.89 is the same number
    // shown to one more place and must not be reported as drift; 1.650 against 1.619 is drift.
    const same = !isNaN(parseFloat(v)) && !isNaN(parseFloat(typed))
                 && Math.abs(parseFloat(v) - parseFloat(typed)) <= 1e-9 * Math.max(1, Math.abs(parseFloat(v)));
    if (same) return;
    if (typed !== v) TABLE_DRIFT.push(label + " " + row[0] + " [" + k + "] typed "
                                      + typed + " -> registry " + v);
    out[i] = v;
  });
  return out;
}
// ---------- load the PUBLISHED matrix (julia/tier0_ec_matrix.csv) ----------
// Table S5 and every median/count the prose quotes are computed from this file, not typed.
// They were typed until 2026-08-25, and had drifted the moment the solver was corrected: the
// table still read 6.0 / 11/50 / 17/50 / 21/50 / 14/50 / 34/50 while the model gave
// 6.1 / 12 / 18 / 20 / 15 / 33. Same defect Tables S3 and S4 had, one table along.
const MAT = fs.readFileSync(path.join(__dirname, "julia", "tier0_ec_matrix.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n");
const MHDR = splitCSV(MAT[0]);
const MROW = MAT.slice(1).map(splitCSV);
const mcol = (n) => { const i = MHDR.indexOf(n);
  if (i < 0) throw new Error("tier0_ec_matrix.csv has no column " + n); return i; };
function matStats(key, carrier) {
  const ci = carrier ? mcol("carrier") : -1;
  const v = MROW.filter(r => !carrier || r[ci] === carrier)
                .map(r => Number(r[mcol(key)])).filter(x => !isNaN(x)).sort((a, b) => a - b);
  const n = v.length;
  if (!n) throw new Error("no rows for " + key + "/" + carrier);
  return { n, median: n % 2 ? v[(n - 1) / 2] : (v[n / 2 - 1] + v[n / 2]) / 2,
           ge25: v.filter(x => x >= 25).length, ge50: v.filter(x => x >= 50).length };
}
// ---------- the migration-free Fick layer, for the S7 physics comparison ----------
const FICK = fs.readFileSync(path.join(__dirname, "julia", "tier0_matrix.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n");
const FHDR = splitCSV(FICK[0]);
const FROW = FICK.slice(1).map(splitCSV);
const fcol = (n) => { const i = FHDR.indexOf(n);
  if (i < 0) throw new Error("tier0_matrix.csv has no column " + n); return i; };
const fickCount = (key, thr) => FROW.filter(r => Number(r[fcol(key)]) >= thr).length;

// ---------- concentration basis (chemistry audit 2026-10-06) ----------
// Every concentration is moles over the stated liquid volume. A reagent charged neat or by mass adds volume that basis
// does not count, so the value is an upper bound; the correction is largest for the four rows below (a neat carbamate,
// its amide analogue, a neat acid, and four equivalents of sulfuric acid). Each ceiling is scaled in proportion to C.
const VOL_ROWS = ["Shono oxidation (N-acyliminium capture)", "Shono alpha-methoxylation of amides",
                  "Kolbe homocoupling of 10-undecenoate", "Ritter-type C(sp3)-H amination"];
const VOL_F = 0.8;
const ARCH7 = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"];
const ARCH7_NM = { natural: "unstirred", stirred: "stirred", flow: "recirculating-flow", anec: "ANEC",
                   micro: "microfluidic", rde: "RDE", rce: "rotating-cylinder" };
function volBasisSentence() {
  const ri = mcol("reaction");
  for (const n of VOL_ROWS) if (!MROW.some(r => r[ri] === n)) throw new Error("concentration-basis row missing: " + n);
  const moves = [];
  for (const k of ARCH7) for (const thr of [25, 50]) {
    const v = MROW.map(r => Number(r[mcol(k)]) * (VOL_ROWS.includes(r[ri]) ? VOL_F : 1));
    const base = MROW.filter(r => Number(r[mcol(k)]) >= thr).length, sc = v.filter(x => x >= thr).length;
    if (base !== sc) moves.push("the " + ARCH7_NM[k] + " \u2265" + thr + " mA cm\u207b\u00b2 count from " + base + " to " + sc);
  }
  return " Each concentration is the moles charged over the stated liquid volume; a reagent charged neat or by mass adds " +
    "volume that basis does not count, so the value is an upper bound, by up to about a fifth for the four rows where that " +
    "volume is largest (" + VOL_ROWS.map(n => n.replace(/ \(.*$/, "")).join("; ") + "). Lowering those four by " +
    Math.round(100 * (1 - VOL_F)) + "% " + (moves.length ? "moves " + moves.join(", ") : "moves no threshold count in any architecture") + ".";
}

// ---------- solvent-property exposure (results/solvent_property_sensitivity.json) ----------
// The S5.5 sentence quoting this band was typed and had drifted three ways at once: it said
// eleven rows where the model flags 13, "at most two entries of fifty" where the worst movement
// is 3, and a baseline of 11-17-21-31-36-36 that predates two solver corrections. It went
// unnoticed because G-SOLV (figs/analysis_solvent_property_sensitivity.py) is in no runner.
// Emitted from the JSON now, so the prose cannot disagree with the sweep that produced it.
const SP = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "solvent_property_sensitivity.json"), "utf8"));
const NUMW = ["zero","one","two","three","four","five","six","seven","eight","nine","ten",
              "eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen"];
const numw = (n) => NUMW[n] || String(n);
const spSpan = () => SP.per_arch_span[0]
  .map((lo, i) => lo === SP.per_arch_span[1][i] ? String(lo)
                  : lo + "\u2013" + SP.per_arch_span[1][i]).join(" / ");

// ---------- the mediated EC' matrix, for Table S6 ----------
// Same rule as Table S5: the numeric columns are computed, never typed. They had drifted badly --
// the chloride/ethylene row printed "392 -> 789" against a model that gives 196 -> 394, a clean
// factor of two left over from an earlier migration convention.
const MEDC = fs.readFileSync(path.join(__dirname, "julia", "mediated_ec_matrix.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n");
// ---- the S5.2 termination census, COMPUTED from the matrix (it was typed until 2026-09-05, and the
// ethylene-D re-solve moved "0.13% ... 39 of 48" to "0.14% ... 35 of 48" behind a green build;
// G-ECBAND caught it). Same parse as that gate: the c_red/cb value the limiter string records.
const sciX = (v) => { const [m, e] = Number(v).toExponential(0).split("e"); return m + " × 10" + String(Number(e)).replace("-", "⁻").replace(/\d/g, (c) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[+c]); };
const CENSUS = (() => {
  const all = MEDC.slice(1);                        // MEDC is already split into lines
  // pass 15: only the cells whose published value IS the concentration-control result (path = c-control); the others
  // keep the ramp's value because the walk that followed did not rise above their k = 0 floor (run_mediated.jl accept rule)
  const rows = all.filter(ln => /,"?c-control"?\s*$/.test(ln));   // the path field is quoted in the CSV
  if (!rows.length) throw new Error("S5.2 census: no mediated cell has path c-control -- the filter no longer matches the matrix");
  const fr = [];
  let ncoll = 0;
  for (const ln of rows) {
    const m = /c_red\/cb ([0-9.eE+-]+)/.exec(ln);
    if (m) fr.push(100 * parseFloat(m[1]));
    else if (/,"?collapse \(c-control\)/.test(ln)) { fr.push(0.1); ncoll += 1; }   // crossed 1e-3 exactly: at the criterion
  }
  if (fr.length !== rows.length) throw new Error("S5.2 census: " + (rows.length - fr.length) + " mediated cell(s) carry neither a plateau value nor a collapse label");
  return { nall: String(all.length), n: String(rows.length), lo: Math.min(...fr).toFixed(2), hi: Math.max(...fr).toFixed(1),
           n028: String(fr.filter(v => v <= 0.28).length), ncoll: String(ncoll) };
})();
// ---- plateaus that stop short of full depletion (results/plateau_continuation.json, G-PLATEAU): each is walked on
// to the 1e-3 criterion in an isolated solve and the change in current recorded.
const PC = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "plateau_continuation.json"), "utf8"));
const plateauSentence = () => {
  if (!PC.cells.length) return "";
  const rx = [...new Set(PC.cells.map(c => c.reaction))];
  if (rx.length !== 1 || rx[0] !== "Thioether -> sulfone (kilo-scale)") throw new Error("the shallow plateaus are no longer the thioether cells the text names: " + JSON.stringify(rx));
  const _sub = PC.cells.map(c => { const m = /c_sub\/cb ([0-9.eE+-]+)/.exec(ecCell(c.reaction, c.reactor).limiter);
    if (!m) throw new Error("plateau cell without a substrate depletion: " + c.reactor); return 100 * parseFloat(m[1]); });
  if (Math.min(..._sub) < 1) throw new Error("a thioether plateau cell now has its substrate exhausted (< 1% of bulk); reword S5.2");
  return "The " + numWord(PC.cells.length) + " cells above " + (100 * PC.threshold_c_red_over_bulk).toFixed(0) + "% all belong to the chloride-mediated thioether oxidation in its thickest films, where the thioether is drawn down to " + Math.min(..._sub).toFixed(0) + "–" + Math.max(..._sub).toFixed(0) + "% of its bulk value at the electrode, so regeneration in the film slows and the current flattens before the mediator is exhausted; walking each on to the 10⁻³ criterion with the plateau test switched off moves its current by at most " + (100 * PC.max_abs_rel_change).toFixed(1) + "%.";
};
const EHDR = splitCSV(MEDC[0]);
const ecol = (n) => { const i = EHDR.indexOf(n);
  if (i < 0) throw new Error("mediated_ec_matrix.csv has no column " + n); return i; };
const EROW = MEDC.slice(1).map(splitCSV);
// ---- the log-log slope of each mediated row against the film, computed here so that the
// manuscript's pointer to this table resolves to content rather than only to a heading.
// Same construction as figs/model_medians.mediated_delta_slopes: least squares of ln(i_EC) on
// ln(delta) over the rows the solver flags ok, which is the model's own convergence flag.
const MED_SLOPES = (() => {
  const by = {};
  EROW.forEach(r => {
    if (r[ecol("flag")] !== "ok") return;
    (by[r[ecol("reaction")]] = by[r[ecol("reaction")]] || [])
      .push([Math.log(Number(r[ecol("delta_um")])), Math.log(Number(r[ecol("i_ec_mAcm2")]))]);
  });
  const out = {};
  for (const k of Object.keys(by)) {
    const v = by[k], n = v.length;
    const mx = v.reduce((a, p) => a + p[0], 0) / n, my = v.reduce((a, p) => a + p[1], 0) / n;
    out[k] = v.reduce((a, p) => a + (p[0] - mx) * (p[1] - my), 0)
           / v.reduce((a, p) => a + (p[0] - mx) * (p[0] - mx), 0);
  }
  return out;
})();
const MED_SLOPE_SENT = (() => {
  const e = Object.keys(MED_SLOPES).map(k => [k, MED_SLOPES[k]]).sort((a, b) => b[1] - a[1]);
  const flat = e.filter(x => x[1] > -0.5), steep = e.filter(x => x[1] <= -0.5);
  const fmt = (x) => "\u2212" + Math.abs(x).toFixed(2);
  const nrx = new Set(EROW.map(r => r[ecol("reactor")])).size;
  return "Fitting ln i_lim against ln \u03b4 across the " + nrx + " archetype films "
    + "separates the rows the film governs from the rows it does not: " + flat.length + " of the "
    + e.length + " are nearly flat (" + (flat.length <= 2 ? flat.map(x => fmt(x[1])).join(" and ")
        : flat.slice(0, -1).map(x => fmt(x[1])).join(", ") + " and " + fmt(flat[flat.length - 1][1])) + "; a shallow slope "
    + "means either that the film barely sets the ceiling or that the row changes regime across the films, §S5.5), while the remaining " + steep.length + " span " + fmt(steep[0][1])
    + " to " + fmt(steep[steep.length - 1][1]) + ", approaching the pure-Fick value of \u22121 "
    + "wherever transport of substrate or of mediator sets the ceiling.";
})();
function ecCell(rxn, reactor) {
  const r = EROW.find(x => x[ecol("reaction")] === rxn && x[ecol("reactor")] === reactor);
  if (!r) throw new Error("mediated_ec_matrix.csv has no cell " + rxn + " / " + reactor);
  return { xk: Number(r[ecol("xk_um")]), t0: Number(r[ecol("i_tier0_mAcm2")]),
           ec: Number(r[ecol("i_ec_mAcm2")]), limiter: r[ecol("limiter")] };
}
// Display conventions already used by this table: x_k to one decimal below 100, currents to a
// whole number at and above 10.
const fxk  = (v) => !isFinite(v) ? "∞" : v >= 100 ? String(Math.round(v)) : v.toFixed(1);   // k = 0: no reaction layer
const fcur = (v) => v >= 10  ? String(Math.round(v)) : v >= 0.2 ? v.toFixed(1) : v.toPrecision(2);   // pass 8: 0.027 printed as 0.0
// ---- S5.2 / S5.5 mediated-matrix facts, COMPUTED (they were typed until 2026-09-07 and had been stale
// since the batch films moved: "delta/x_k ~ 43 stirred", "at 128", "104.7", "amplifications x1.0 to x27",
// "2/8 to 3/8 (>=25: 2/8 to 4/8)" all described the 100 um / 300 um films behind green gates)
const EC = EROW.map(r => ({ rxn: r[ecol("reaction")], reactor: r[ecol("reactor")], delta: Number(r[ecol("delta_um")]),
                            xk: Number(r[ecol("xk_um")]), t0: Number(r[ecol("i_tier0_mAcm2")]), ec: Number(r[ecol("i_ec_mAcm2")]),
                            sav: Number(r[ecol("i_saveant_mAcm2")]), cap: Number(r[ecol("i_subcap_mAcm2")]),
                            limiter: r[ecol("limiter")], path: r[ecol("path")] }));
// The S5.5 bracket: every mediated cell replaced by its closed-form envelope min(Saveant, substrate supply)
// and, separately, by its Stage-0 floor; the >=25 count per architecture over the three variants gives the
// band. Same construction as the gate that checks it (it was a typed "10-12, 12-14, ..." until 2026-09-07).
// (a function, not an IIFE: ARCH and ORDERING_TEXT are defined further down; it is called where the sentence is built)
const bracket = () => {
  const label = Object.fromEntries(ARCH.map(([lab, k]) => [k, lab]));
  const medSet = new Set(EC.map(c => c.rxn));
  const out = [];
  for (const [, k] of ARCH) {
    const base = MROW.filter(r => !medSet.has(r[mcol("reaction")])).map(r => Number(r[mcol(k)]));
    // the solver writes the microfluidic label with "um"; the SI prints it with the Greek letter
    const mlabel = k === "micro" ? "Microfluidic cell (25 um gap)" : label[k];
    const cells = EC.filter(c => c.reactor === mlabel);
    if (cells.length !== N_MED) throw new Error("bracket: " + k + " has " + cells.length + " mediated cells (label " + mlabel + ")");
    const n = (vals) => base.concat(vals).filter(v => v >= 25).length;
    const v = [n(cells.map(c => c.ec)), n(cells.map(c => c.t0)), n(cells.map(c => Math.min(c.sav, c.cap)))];
    out.push(Math.min(...v) + "\u2013" + Math.max(...v));
  }
  const FIN = EC.filter(c => c.sav > 0), above = FIN.filter(c => c.ec > Math.min(c.sav, c.cap)).length, capC = EC.filter(c => c.ec > c.cap), aboveCap = capC.length;
  // chemistry audit pass 7: three groups, not two. The cells left with a few percent of substrate at the wall (Hofmann thin
  // films, the thioether's batch films) are substrate-limited, not carried past the cap by the carrier; and the four ethylene
  // cells that end on the collapse criterion record no wall concentration at all (the old range printed NaN).
  const cs_ = (c) => { const m = /c_sub\/cb ([0-9.eE+-]+)/.exec(c.limiter); return m ? Number(m[1]) : null; };
  const exh = capC.filter(c => { const v = cs_(c); return v !== null && v < 1e-2; });
  const mig = capC.filter(c => !exh.includes(c) && c.ec / c.t0 >= 1.9 && c.ec / c.t0 <= 2.2);
  const near = capC.filter(c => !exh.includes(c) && !mig.includes(c));
  // a substrate-supply cell must be insensitive to k: read the tenfold sweep for each (results/rate_constant_cells.csv)
  const up10 = near.map(c => { const at = (tag) => { const r = KCELLS.find(x => x[0] === c.rxn && x[1] === tag && (x[2] === c.reactor ||
      (x[2].startsWith("Microfluidic") && c.reactor.startsWith("Microfluidic")))); if (!r) throw new Error("S5.5: no k-sweep cell " + c.rxn + " / " + c.reactor + " / " + tag); return Number(r[4]); };
    return at("mul10") / at("base") - 1; });
  if (near.some(c => cs_(c) === null))
    throw new Error("S5.5: an above-cap cell records no wall concentration");
  // 2026-10-07: being above the planar cap is not by itself being held there. The substrate-limited cells are the ones a
  // tenfold larger k barely moves; an above-cap cell that responds to k as a kinetic cell does is reported as such (the
  // Hofmann row's recirculating-flow cell at its measured constant).
  const nearSub = near.filter((c, i) => up10[i] <= 0.15), nearKin = near.filter((c, i) => up10[i] > 0.15);
  const up10Sub = up10.filter(v => v <= 0.15), up10Kin = up10.filter(v => v > 0.15);
  const flo = [];
  const SHORT = { "Br-mediated Hofmann rearrangement": "the Hofmann rearrangement", "Thioether -> sulfone (kilo-scale)": "the thioether oxidation",
    "Cl-mediated ethylene epoxidation": "the ethylene epoxidation", "Br- oxidation / electrophilic bromination": "the anisole bromination" };
  const shortOf = (r) => { if (SHORT[r]) return SHORT[r]; if (r.startsWith("Amidyl-radical")) return "the amidyl C–H amination";
    throw new Error("S5.5: no short name for " + r); };
  const rowsOf = (cs) => listAnd(Array.from(new Set(cs.map(c => c.rxn))).map(shortOf));
  const nv = nearSub.map(cs_), xk = nearSub.map(c => c.xk);
  const nameCell = (c) => shortOf(c.rxn) + " in the " + (WALLNAME[c.reactor] || c.reactor).replace(/-/g, " ") + " cell";
  return { text: out.slice(0, -1).join(", ") + " and " + out[out.length - 1], above, aboveCap, n: EC.length, nFin: FIN.length,
           exh: exh.length, near: nearSub.length, nearRows: rowsOf(nearSub), nearLo: Math.min(...nv), nearHi: Math.max(...nv),
           xkLo: Math.min(...xk), xkHi: Math.max(...xk), up10: Math.max(...up10Sub),
           kinN: nearKin.length, kinCells: (new Set(nearKin.map(c => c.reactor)).size === 1 && nearKin.length > 1
             ? listAnd(Array.from(new Set(nearKin.map(c => c.rxn))).map(shortOf)) + " in the " + (WALLNAME[nearKin[0].reactor] || nearKin[0].reactor).replace(/-/g, " ") + " cell"
             : listAnd(nearKin.map(nameCell))), kinUp: up10Kin.length ? Math.min(...up10Kin) : 0,
           mig: mig.length, migRows: rowsOf(mig) };
};
const ecAmp = (c) => c.ec / c.t0;
const ecRows = (frag) => EC.filter(c => c.rxn.includes(frag));
const ecOne = (frag, reactor) => { const c = EC.find(x => x.rxn.includes(frag) && x.reactor === reactor); if (!c) throw new Error("no EC cell " + frag + " / " + reactor); return c; };
const fRange = (vals, f) => f(Math.min(...vals)) + "\u2013" + f(Math.max(...vals));
const AMP_ALL = "\u00d7" + Math.min(...EC.map(ecAmp)).toFixed(1) + " to \u00d7" + Math.round(Math.max(...EC.map(ecAmp)));
const ecCount = (reactor, thr, key) => EC.filter(c => c.reactor === reactor && c[key] >= thr).length;
const HOF_ST = ecOne("Hofmann", "Stirred batch"), HOF_UN = ecOne("Hofmann", "Unstirred batch");
const ACT = ecRows("ACT-mediated"), HMF = ecRows("HMF"), NHPI = ecRows("NHPI");
// the NHPI row by film class, asserted so the S5.5 sentence that names the classes cannot outlive the matrix
const NHPI_THICK = NHPI.filter(c => ["Unstirred batch", "Stirred batch", "Recirculating flow cell"].includes(c.reactor));
const NHPI_THIN = NHPI.filter(c => ["Microfluidic cell (25 \u03bcm gap)", "Microfluidic cell (25 um gap)", "RDE 1600 rpm", "Rotating cylinder 3000 rpm"].includes(c.reactor));
const NHPI_ANEC = NHPI.find(c => c.reactor === "ANEC flow cell");
if (NHPI_THICK.length !== 3 || NHPI_THIN.length !== 3 || !NHPI_ANEC) throw new Error("S5.5: the NHPI row does not split into three thick films, the ANEC film and three thin films");
const batchOf = (rows) => rows.filter(c => /batch/.test(c.reactor));
const WALL = EC.filter(c => /^newton-wall/i.test(c.limiter));
const WALLNAME = { "Unstirred batch": "unstirred-batch", "Stirred batch": "stirred-batch", "Recirculating flow cell": "recirculating-flow",
                   "ANEC flow cell": "ANEC", "Microfluidic cell (25 um gap)": "microfluidic", "RDE 1600 rpm": "rotating-disk",
                   "Rotating cylinder 3000 rpm": "rotating-cylinder" };
const listAnd = (xs) => xs.length <= 1 ? xs.join("") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1];
// the wall cells, named by system (2026-10-05: the triarylamine row, reclassified as a mediator and solved at k = 0, walls
// in every architecture exactly as the catalyst rows do in the k = 0 layer; the value published is still the plateau)
const WALL_SYS = { "Cl-mediated ethylene": "the Cl\u207b/ethylene system", "Oxazole synthesis": "the triarylamine-mediated oxazole synthesis, solved at k = 0" };
const wallSysOf = (rxn) => { const k = Object.keys(WALL_SYS).find(x => rxn.includes(x)); if (!k) throw new Error("the S5.2 wall sentence has no name for wall cells of " + rxn); return k; };
if (WALL.length === 0) throw new Error("the S5.2 wall sentence expects wall cells; the matrix has none");
const WALL_SENT = (["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"][WALL.length] || String(WALL.length)) + " cells \u2014 " + listAnd(Object.keys(WALL_SYS).map(k => {
    const w = WALL.filter(c => wallSysOf(c.rxn) === k); if (!w.length) return null;
    const names = w.map(c => WALLNAME[c.reactor] || (() => { throw new Error("no wall name for " + c.reactor); })());
    return (w.length === new Set(EC.map(c => c.reactor)).size ? "every architecture" : "the " + listAnd(names) + " architectures") + " of " + WALL_SYS[k];
  }).filter(Boolean)) + " \u2014";
// The S5.2 passage names the stiffest finite-k cell, the one that most tests the walk. Since the Hofmann row took its measured
// rate constant (3.3 M-1 s-1, 2026-10-07) that cell is the anisole bromination in the unstirred beaker; the assertion below
// keeps it so and requires it to be reached by the ordinary walk.
// The Cl4NHPI row is the anion in both layers (carrier_charge.csv, z = -1; run_mediated.jl since chemistry audit pass 1);
// the factor the anion's migration adds to the k = 0 ceiling is read from the k = 0 layer.
const NPM = fs.readFileSync(path.join(__dirname, "julia", "all50_np_matrix.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);
// pass 15 (codebase audit): the 50-reaction Stage-1 layer evaluates its collapse criterion at the first cell centre
// (0.5 % of delta into the film), so every neutral cell reads a fixed fraction above the exact Fick limit. Measured here
// from the matrix itself and stated in S5.3; no neutral cell lies inside that margin above a threshold.
const NP_NEUT = (() => { const h = NPM[0], iz = h.indexOf("z_carrier"), im = h.indexOf("migration_factor"), ii = h.indexOf("i_np_mAcm2");
  const r = NPM.slice(1).filter(x => Number(x[iz]) === 0); const f = r.map(x => Number(x[im]));
  if (!r.length || Math.max(...f) - Math.min(...f) > 1e-9 || Math.max(...f) > 1.01) throw new Error("S5.3: the neutral cells of the Stage-1 layer do not share one small offset");
  if (r.some(x => [25, 50].some(t => Number(x[ii]) >= t && Number(x[ii]) < t * f[0]))) throw new Error("S5.3 says the offset moves no count; a neutral cell sits inside it above a threshold");
  return { n: r.length, pct: (100 * (f[0] - 1)).toFixed(2) }; })();
// The mesh-refinement bound of S5.2 and S10 is the audit's own G12 result (julia/audit_gates.csv: the production rows re-solved
// at N = 180 with a 7.5x finer continuation). It was typed as "at most 0.01%" and went stale when the Wacker row's rate constant
// changed (2026-10-05, night; that row now moves 0.29%). Read here, and asserted to leave every published threshold count alone.
const AG = fs.readFileSync(path.join(__dirname, "julia", "audit_gates.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);
const G12 = AG.slice(1).filter(r => r[AG[0].indexOf("gate")] === "G12");
if (G12.length !== 2 || G12.some(r => r[AG[0].indexOf("pass")] !== "true")) throw new Error("audit_gates.csv: expected two passing G12 rows");
const G12_MAX = Math.max(...G12.map(r => Math.abs(Number(r[AG[0].indexOf("err_pct")]))));
const G12_TXT = G12_MAX < 0.01 ? "0.01" : G12_MAX.toFixed(2);
// S5.6 quotes the commuting-bound and Saveant comparisons; read from the same audit file (they were typed -0.13% and +1.1%,
// and moved when the EC' mesh and the Saveant depletion correction changed).
const agErr = (gate, desc) => { const r = AG.slice(1).find(x => x[AG[0].indexOf("gate")] === gate && x[AG[0].indexOf("description")].includes(desc));
  if (!r || r[AG[0].indexOf("pass")] !== "true") throw new Error("audit_gates.csv: no passing " + gate + " row for " + desc);
  const v = Number(r[AG[0].indexOf("err_pct")]); return (v < 0 ? "\u2212" : "+") + Math.abs(v).toFixed(2); };
const AG_COMMUTE = agErr("G5", "commuting bound"), AG_SAV = agErr("G6", "Saveant");
// S7: what migration ALONE buys is the k = 0 layer against its own Fick column (all50_np_matrix.csv). The published counts
// also carry the homogeneous EC' step, so comparing them with the Fick matrix (as this sentence once did) credited migration
// with what the EC' source does (chemistry audit, pass 4).
const NPH = NPM[0];
const npCol = (n) => { const i = NPH.indexOf(n); if (i < 0) throw new Error("all50_np_matrix.csv has no column " + n); return i; };
const npCells = (lab) => { const c = NPM.slice(1).filter(r => r[npCol("reactor")] === lab.replace(/\u03bc/g, "u"));
  if (c.length !== 50) throw new Error("k = 0 layer: " + lab + " has " + c.length + " rows, not 50"); return c; };
const npCount = (lab, c, t) => npCells(lab).filter(r => Number(r[npCol(c)]) >= t).length;
const MIG = (() => { const c = npCells("Unstirred batch"); const f = c.map(r => Number(r[npCol("migration_factor")]));
  const z = c.map(r => Number(r[npCol("z_carrier")])); const dbl = c.filter((r, i) => f[i] > 1.9);
  if (dbl.some(r => Number(r[npCol("z_carrier")]) !== -1)) throw new Error("S7: a row whose ceiling migration doubles is not an anion");
  return { neutral: z.filter(x => x === 0).length, lt5: f.filter(x => x < 1.05).length, dbl: dbl.length, max: Math.max(...f) }; })();
// S7: O2, the stirred film's proxy, against the median carrier diffusivity of the set (it was typed "about twice as fast ...
// by roughly 20-30%"); delta ~ D^(1/3) laminar, D^(1/2) penetration theory.
const O2PROXY = (() => { const D = csv.slice(1).map(splitCSV).map(r => Number(r[col("D_cm2s")])).sort((a, b) => a - b);
  if (D.length !== 50) throw new Error("O2 proxy: expected 50 carrier diffusivities");
  const r = 2.10e-5 / ((D[24] + D[25]) / 2);   // O2 in water, Cussler Table 5.2-1 p. 127
  if (!(r > 1)) throw new Error("O2 does not diffuse faster than the median carrier; the S7 direction claim fails");
  return { ratio: r.toFixed(1), lo: (100 * (1 - Math.pow(r, -1 / 3))).toFixed(0), hi: (100 * (1 - Math.pow(r, -1 / 2))).toFixed(0) }; })();
// S7: the stirred and recirculating-flow archetypes are single fixed films; the ordering between them inverts only below the
// flow film (it was typed "below about 86 um ... a parallel-plate flow cell", a retired archetype)
const FLOW_FILM_UM = (() => { const d = [...new Set(EC.filter(c => c.reactor === "Recirculating flow cell").map(c => c.delta))];
  const st = [...new Set(EC.filter(c => c.reactor === "Stirred batch").map(c => c.delta))];
  if (d.length !== 1 || st.length !== 1 || !(st[0] > d[0])) throw new Error("S7: the stirred and flow films are not single fixed values in that order");
  return d[0].toFixed(1); })();
// ---- S7: how much thinner the stirred film would have to be for the stirred median to reach 25 mA cm-2. Each row's
// ceiling is interpolated in log-log across its own five fixed films (julia/delta_bounds.csv, delta_ref_um), and the film
// at which the median over the fifty rows reaches 25 is found by bisection.
const STIR_THIN = (() => {
  const L = fs.readFileSync(path.join(__dirname, "julia", "delta_bounds.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV), h = L[0];
  const FILM = { natural: "Unstirred batch", stirred: "Stirred batch", flow: "Recirculating flow cell", anec: "ANEC flow cell", micro: "Microfluidic cell (25 um gap)" };
  const dref = new Map(L.slice(1).map(r => [r[h.indexOf("reaction")] + "|" + r[h.indexOf("reactor")], Number(r[h.indexOf("delta_ref_um")])]));
  const pts = MROW.map(r => Object.entries(FILM).map(([k, lab]) => {
    const d = dref.get(r[mcol("reaction")] + "|" + lab); if (!d) throw new Error("S7: delta_bounds.csv lacks " + r[mcol("reaction")] + " / " + lab);
    return [Math.log(d), Math.log(Number(r[mcol(k)]))]; }).sort((a, b) => a[0] - b[0]));
  const at = (p, x) => { for (let i = 1; i < p.length; i++) if (x <= p[i][0]) { const f = (x - p[i - 1][0]) / (p[i][0] - p[i - 1][0]); return p[i - 1][1] + f * (p[i][1] - p[i - 1][1]); } return p[p.length - 1][1]; };
  const medAt = (d) => { const v = pts.map(p => Math.exp(at(p, Math.log(d)))).sort((a, b) => a - b); return (v[24] + v[25]) / 2; };
  let lo = 12.5, hi = 200;
  if (!(medAt(hi) < 25 && medAt(lo) > 25)) throw new Error("S7: the stirred-film question is not bracketed by the fixed films");
  for (let i = 0; i < 80; i++) { const m = Math.sqrt(lo * hi); if (medAt(m) > 25) lo = m; else hi = m; }
  return 200 / Math.sqrt(lo * hi); })();
// ---- S5.2: the stiffest cell's front. Br2 is the only consumer of the anisole, so the substrate the front consumes is
// supplied across delta - x_f, which bounds x_f <= delta (1 - i_subcap/i_ec).
const BROM_UN = ecOne("electrophilic bromination", "Unstirred batch");
const BROM_XF_MAX = BROM_UN.delta * (1 - BROM_UN.cap / BROM_UN.ec);
const BROM_CSUB = (() => { const m = /c_sub\/cb ([0-9.eE+-]+)/.exec(BROM_UN.limiter);
  if (!m || Number(m[1]) > 1e-2) throw new Error("S5.2: the bromination unstirred cell no longer exhausts its substrate at the wall: " + BROM_UN.limiter);
  return Number(m[1]); })();
if (!(BROM_UN.t0 < 25 && BROM_UN.ec >= 25)) throw new Error("S5.2 says the coupling carries the unstirred bromination cell across 25 mA cm-2: " + BROM_UN.t0 + " -> " + BROM_UN.ec);
// the bromine behind the front, read from the drawn ANEC profile (main-text Fig. 6d), in M and as a multiple of the bromide bulk
const BROM_COX = (() => { const P = fs.readFileSync(path.join(__dirname, "julia", "mediated_ec_profiles.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);
  const h = P[0], rows = P.slice(1).filter(r => r[h.indexOf("short")] === "Bromination");
  if (rows.length < 50) throw new Error("S5.2: no bromination profile in mediated_ec_profiles.csv");
  const mx = Math.max(...rows.map(r => Number(r[h.indexOf("c_ox_norm")]))), cm = Number(rows[0][h.indexOf("C_med_molm3")]);
  if (!(mx > 1)) throw new Error("S5.2 says the bromine behind the drawn front exceeds the bromide bulk; the profile gives " + mx);
  return { ratio: mx, M: mx * cm / 1000, cm: cm, cs: Number(rows[0][h.indexOf("C_S_molm3")]) }; })();
const SUP = (x) => { const e = Math.floor(Math.log10(x)), m = x / Math.pow(10, e); const sup = String(e).replace("-", "⁻").replace(/\d/g, d => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]); return (m >= 9.95 ? "10" : m.toFixed(1)) + " × 10" + sup; };
// S8: which concentrated aqueous conductivities the CRC p. 5-71 table supports, read from the registry (it was typed "four
// aqueous rows are derived"; one is measured, one derived, and the others are assumptions)
const AQ_COND_TXT = (() => { const L = fs.readFileSync(PROV_CSV, "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV); const h = L[0];
  const rows = L.slice(1).filter(r => r[h.indexOf("category")].startsWith("6") && / aq$/.test(r[h.indexOf("parameter")]) && /5-71/.test(r[h.indexOf("locator")]));
  const live = new Set(JSON.parse(fs.readFileSync(path.join(__dirname, "results", "registry_liveness.json"), "utf8")).live_parameters);
  const pub = rows.filter(r => live.has(r[h.indexOf("parameter")]));
  if (!pub.length || pub.some(r => !["measured", "derived"].includes(r[h.indexOf("provenance_class")]))) throw new Error("S8: a published p. 5-71 aqueous row is not measured or derived");
  return "the published " + (pub.length === 1 ? "row" : "rows") + " that table reaches, " + listAnd(pub.map(r => r[h.indexOf("parameter")].replace(/ aq$/, "") + " (" + r[h.indexOf("provenance_class")] + ")")) + ", " + (pub.length === 1 ? "is" : "are") + " corroborated by it"; })();

const NHPI_MIG = (() => { const h = NPM[0], ri = h.indexOf("reaction"), zi = h.indexOf("z_carrier"), mi = h.indexOf("migration_factor");
  const r = NPM.slice(1).filter(x => x[ri] === "NHPI-mediated allylic C-H -> enone");
  if (r.length !== 7 || r.some(x => Number(x[zi]) !== -1)) throw new Error("S5.5: the NHPI row is not the anion in all seven k = 0 cells");
  const f = r.map(x => Number(x[mi])); if (Math.max(...f) - Math.min(...f) > 1e-6) throw new Error("S5.5: the NHPI migration factor varies across films");
  return f[0]; })();
const STIFF = EC.filter(c => c.xk > 0 && isFinite(c.xk)).reduce((a, c) => (c.delta / c.xk > a.delta / a.xk ? c : a));
if (STIFF !== BROM_UN || /newton-wall|continu|tracked/i.test(STIFF.limiter + " " + (STIFF.path || "")))
  throw new Error("S5.2 names the unstirred anisole bromination as the stiffest cell, reached by the ordinary walk; the matrix says " + STIFF.rxn + "/" + STIFF.reactor + "/" + STIFF.limiter + "/" + STIFF.path);
// S5.5 (2026-10-07): the Hofmann row at the constant measured for aqueous HOBr with propionamide, 3.3 M-1 s-1 (Heeb et al.,
// Water Res. 2014, Table 6). Its reaction layer then lies inside the two batch films and is wider than every thin one: the
// batch cells amplify strongly with the amide drawn down but not exhausted at the wall, and in the thin cells the bromine
// leaves the film before it reacts, so the row sits at the bromide's migration-only (k = 0) ceiling. Each clause asserted.
const npK0 = (rxn, reactor) => { const h = NPM[0], r = NPM.slice(1).find(x => x[h.indexOf("reaction")] === rxn && x[h.indexOf("reactor")] === reactor);
  if (!r) throw new Error("no k = 0 cell " + rxn + " / " + reactor); return Number(r[h.indexOf("i_np_mAcm2")]); };
// the thin films are the three sub-20 um ones; the ANEC film (36 um) also lies inside x_k but sits well above the k = 0
// ceiling (delta/x_k ~ 0.9: part of the bromine reacts in it), so the sentence does not count it among them
const HOF = ecRows("Hofmann"), HOF_BATCH = HOF.filter(c => /batch/.test(c.reactor)), HOF_THIN = HOF.filter(c => c.delta < 20);
const HOF_ST_CS = (() => { const m = /c_sub\/cb ([0-9.eE+-]+)/.exec(HOF_ST.limiter); return m ? Number(m[1]) : NaN; })();
const HOF_THIN_K0 = HOF_THIN.map(c => c.ec / npK0(c.rxn, c.reactor) - 1);
if (HOF_BATCH.length !== 2 || HOF_BATCH.some(c => c.xk >= c.delta) || !(HOF_ST_CS > 1e-2 && HOF_ST_CS < 0.2) || HOF_THIN.length !== 3 || HOF_THIN.some(c => c.xk <= c.delta)
    || HOF_THIN_K0.some(v => v < -0.005 || v > 0.10))
  throw new Error("S5.5: the Hofmann sentence (reaction layer inside the batch films and wider than the thin ones; amide drawn down but not exhausted; thin cells at the k = 0 ceiling) no longer matches the matrix: " + HOF_ST_CS + ", " + HOF_THIN_K0.join(", "));
if (!(BROM_UN.ec / npK0(BROM_UN.rxn, BROM_UN.reactor) < 1.05)) throw new Error("S5.2 says the unstirred bromination cell sits at the bromide's migration-only ceiling: " + BROM_UN.ec + " vs " + npK0(BROM_UN.rxn, BROM_UN.reactor));
const WALL_ETH = WALL.filter(c => /ethylene/.test(c.rxn)), WALL_OXA = WALL.filter(c => /^Oxazole/.test(c.rxn));
if (WALL_ETH.length + WALL_OXA.length !== WALL.length || WALL_OXA.length !== 7 || WALL_ETH.some(c => c.delta >= 20)
    || WALL.some(c => c.path !== "direct-ramp" || Math.abs(c.ec / npK0(c.rxn, c.reactor) - 1) > 1e-4))
  throw new Error("S5.2 says the wall cells are the seven oxazole cells and the ethylene epoxidation's thin films, each published at its k = 0 floor");
const WALL_ETH_ADD = (Math.ceil(1e4 * Math.max(...WALL_ETH.map(c => c.cap / c.ec))) / 100).toFixed(2);   // an upper bound is rounded up
// S5.5: where the Hofmann row's 41 um reaction layer sits against each film (pass 15: the flow and ANEC films were missing)
const HOF_FLOW = HOF.find(c => c.reactor === "Recirculating flow cell"), HOF_ANEC = HOF.find(c => c.reactor === "ANEC flow cell");
if (!(HOF_FLOW && HOF_FLOW.delta > HOF_FLOW.xk && HOF_ANEC && HOF_ANEC.delta / HOF_ANEC.xk > 0.5 && HOF_ANEC.delta / HOF_ANEC.xk < 2))
  throw new Error("S5.5 says the Hofmann reaction layer lies inside the flow film and is comparable to the ANEC film");
const HOF_THIN_NAMES = listAnd(HOF_THIN.map(c => WALLNAME[c.reactor] || (() => { throw new Error("no name for " + c.reactor); })()));
// SI display label -> the reaction name the solver writes.
const S6MAP = {
  "Br⁻ / Hofmann rearrangement (80 mM, MeCN)": "Br-mediated Hofmann rearrangement",
  "ACT / alcohol oxidation (25 mM, aq. pH 8.5)": "ACT-mediated alcohol oxidation (flow, hectogram)",
  "Cl⁻ / ethylene epoxidation (1 M KCl, aq.)": "Cl-mediated ethylene epoxidation",
  "Cl₄NHPI / allylic C–H (33 mM, acetone)": "NHPI-mediated allylic C-H -> enone",
  "ACT / HMF → FDCA (40 mM, aq. pH 10)": "HMF -> FDCA (biomass)",
  "BQ / Wacker–Tsuji (22 mM, MeCN/H₂O)": "BQ-mediated Wacker-Tsuji oxidation",
  "Br⁻ / electrophilic bromination (0.25 M, aq./MeCN)": "Br- oxidation / electrophilic bromination",
  "SCN⁻ / thiocyanation (0.1 M, AcOH/HCOOH)": "Aryl thiocyanation (NH4SCN)",
  "Br⁻ / amidyl C–H amination (40 mM, MeCN/MeOH)": "Amidyl-radical C-H amination (phenanthridinone)",
  "Cl⁻ / thioether → sulfone (14 mM, MeCN/aq. HCl)": "Thioether -> sulfone (kilo-scale)",
  "O₂ / Giese addition (0.27 mM, aq./MeCN)": "Cathodic Giese (R-I + alkene)",
  "Ar₃N / oxazole synthesis (5 mM, MeCN)": "Oxazole synthesis from ketones and acetonitrile",
};
// each label states the row's carrier loading; asserted against the reaction table so a label cannot drift from the
// number the solver uses
for (const [lab, rxn] of Object.entries(S6MAP)) {
  const m = lab.match(/\(([\d.]+) (mM|M)/); if (!m) throw new Error("Table S6 label states no loading: " + lab);
  const c = Number(m[1]) * (m[2] === "mM" ? 1e-3 : 1), r = rxRows.find(x => x[2] === rxn);
  if (!r) throw new Error("Table S6: no reaction-table row " + rxn);
  if (Math.abs(c / Number(r[7]) - 1) > 0.05) throw new Error("Table S6 label " + lab + " states " + c + " M; the reaction table gives " + r[7]);
}
if (Object.keys(S6MAP).length !== N_MED) throw new Error("Table S6 lists " + Object.keys(S6MAP).length + " systems; the reaction table holds " + N_MED + " mediated rows");
// Two rate constants are taken from the exemplar's own operation on a smooth electrode of stated area:
// the smallest k for which the kinetic plateau n_c F C_med (D_ox k C_S)^1/2 carries the current it reports.
const kFloorM = (i_Am2, Cmed_molm3, Dox, Cs_molm3) => 1e3 * Math.pow(i_Am2 / (96485.33212 * Cmed_molm3), 2) / (Dox * Cs_molm3);
const K_THIO = kFloorM(400, 14, 2.6e-9, 100);                               // 40 mA cm-2, 0.1 M thioether, 14 mM chloride (Bottecchia 2022, Fig. 4A)
const GIESE_I = 300 / (84e3 * 4.12e-4);                                      // ~300 C over the ~84 ks charge record (Li/Wilden 2020 Fig. 2 p. 5335) on one 4.12 cm2 rod (ESI p. S5), A m-2
// C_S is the alkyl iodide the exemplar's relay activates, read from the reaction table (it had been the sulfone's 79 mM, typed)
const GIESE_CS = 1000 * Number(csv.slice(1).map(splitCSV).find(r => r[col("reaction")] === "Cathodic Giese (R-I + alkene)")[col("C_substrate_M")]);
const K_GIESE = kFloorM(GIESE_I, 0.266, 2.1e-9, GIESE_CS);
const sci1 = (x) => { const e = Math.floor(Math.log10(x)); const m = x / Math.pow(10, e);
  return (m >= 9.5 ? "1" : m.toFixed(m < 3.95 ? 1 : 0).replace(/\.0$/, "")) + " × 10" + ({ 1: "¹", 2: "²", 3: "³", 4: "⁴" })[m >= 9.5 ? e + 1 : e]; };
if (!(K_THIO > 1e2 && K_THIO < 1e3 && K_GIESE > 1e2 && K_GIESE < 1e3)) throw new Error("the two operation-derived rate constants no longer round up to the adopted 10^3: " + K_THIO + ", " + K_GIESE);
// The limiter column is READ from the row's seven solved cells (chemistry audit pass 4: it was typed, and the Hofmann and
// bromination labels contradicted the solve -- a "mediator plateau" whose substrate is exhausted at a detached front, and a
// "substrate cap" on a row that sits at 2.09x its carrier's Fick bound in every film). Rules, in order: the carrier with its
// migration factor where i/i_Fick sits near 2 in every cell; the commuting bound at k = 0; the substrate where the solve
// exhausts it at the wall (c_sub/cb < 1e-2 in the limiter string: the reaction front has left the wall); otherwise the
// mediator, kinetic where x_k < delta (chemistry audit pass 6: "current above the planar cap" is not that test -- the amidyl
// row's k = 0 bound already exceeds its cap in the thin films, with a fifth of the substrate still at the wall).
const csubOf = (c) => { const m = /c_sub\/cb ([0-9.eE+-]+)/.exec(c.limiter); return m ? Number(m[1]) : null; };
const S6SHORT = { "Unstirred batch": "unstirred", "Stirred batch": "stirred", "Recirculating flow cell": "recirculating flow",
  "ANEC flow cell": "ANEC", "Microfluidic cell (25 \u03bcm gap)": "microfluidic", "Microfluidic cell (25 um gap)": "microfluidic", "RDE 1600 rpm": "RDE", "Rotating cylinder 3000 rpm": "rotating-cylinder" };
function s6Limiter(rxn, k) {
  const cs = EC.filter(c => c.rxn === rxn);
  if (cs.length !== 7) throw new Error("Table S6 limiter: " + rxn + " has " + cs.length + " cells");
  const r = cs.map(c => c.ec / c.t0).sort((a, b) => a - b);
  if (r[0] >= 1.9 && r[r.length - 1] <= 2.2) return "carrier (migration ×" + r[Math.floor(r.length / 2)].toFixed(1) + " in every film)";
  if (k === 0) return "mediator (k = 0: the commuting bound)";
  // chemistry audit pass 7: the substrate also limits a cell whose current reaches its planar supply cap: the reaction sits
  // a few micrometres off the wall, so the substrate diffuses less than delta, and a tenfold larger k raises those cells by
  // at most ~10 % (results/rate_constant_cells.csv), where a kinetic plateau would rise ~3x. The main text's thioether
  // sentence uses the same test, so Table S6, S5.5 and Section 4 classify the same cells.
  const exhC = (c) => { const v = csubOf(c); return v !== null && v < 1e-2; };
  // 2026-10-07: the cap test is confirmed by the tenfold k sweep, not assumed -- an above-cap cell that a tenfold larger k
  // raises by more than 15 % is not held at its supply (the Hofmann row's recirculating-flow cell at its measured constant)
  const kUp10 = (c) => { const at = (tag) => { const r = KCELLS.find(x => x[0] === c.rxn && x[1] === tag && (x[2] === c.reactor ||
      (x[2].startsWith("Microfluidic") && c.reactor.startsWith("Microfluidic")))); if (!r) throw new Error("Table S6 limiter: no k-sweep cell " + c.rxn + " / " + c.reactor + " / " + tag); return Number(r[4]); };
    return at("mul10") / at("base") - 1; };
  const capC_ = (c) => c.ec >= c.cap && kUp10(c) <= 0.15 && c.xk < c.delta;   // pass 15: a cell whose reaction layer is wider than the film is k-insensitive because k is irrelevant there, not because the substrate holds it
  const sub = cs.filter(c => exhC(c) || capC_(c));
  const why = sub.every(exhC) ? "exhausted at the wall" : sub.every(capC_) ? "current at or above its planar supply cap"
            : "exhausted at the wall or at its planar supply cap";
  if (sub.length === cs.length) return "substrate (" + why + " in every film)";
  const rest = cs.filter(c => !sub.includes(c));
  const name = (c) => { const n = S6SHORT[c.reactor]; if (!n) throw new Error("Table S6 limiter: no short name for " + c.reactor); return n; };
  // chemistry audit pass 8: one rule for every mediated cell. A cell whose reaction layer is thicker than the film is
  // transport-limited; every other cell is read against the 10 % plateau test (the earlier x_k < delta shortcut called
  // the NHPI ANEC cell "kinetic" where S5.4 and the profile solve both call it mixed).
  const thin = rest.filter(c => c.xk > c.delta), kin = rest.filter(c => !thin.includes(c));
  const med = r[r.length - 1] < 1.1 ? "transport-limited, little regeneration inside the film"
            : ((() => {
                   // chemistry audit pass 7: "kinetic plateau" only where the current lies within 10 % of
                   // n_c F C_med (D_ox k C_S)^1/2; the Hofmann and amidyl thin films sit 2-3x ABOVE it. The label states
                   // the computed factor and no mechanism: i_lim*delta is constant for those two rows, not for the others.
                   const below = kin.filter(c => c.ec < 0.9 * c.sav), above = kin.filter(c => c.ec > 1.1 * c.sav),
                         at = kin.filter(c => !below.includes(c) && !above.includes(c));
                   const fx = above.map(c => c.ec / c.sav), lo = Math.min(...fx).toFixed(1), hi = Math.max(...fx).toFixed(1);
                   const by = " by a factor of " + (lo === hi ? lo : lo + "–" + hi);
                   const g = [[at, "kinetic plateau"], [below, "below the kinetic plateau"],
                              [above, "above the kinetic plateau"], [thin, "transport-limited (x_k > δ)"]].filter(x => x[0].length);
                   if (g.length === 1) return g[0][1] + (g[0][0] === at || sub.length ? "" : " in every film") + (g[0][0] === above ? "," + by : "");
                   return g.map(x => x[1] + " in the " + listAnd(x[0].map(name)) + (x[0].length > 1 ? " cells" : " cell") + (x[0] === above ? "," + by : "")).join("; "); })());
  return sub.length ? "substrate in the " + listAnd(sub.map(name)) + (sub.length > 1 ? " cells (" : " cell (") + why + "); mediator elsewhere (" + med + ")" : "mediator (" + med + ")";
}
function s6FromMatrix(rows) {
  return rows.map(row => {
    const rxn = S6MAP[row[0]];
    if (!rxn) throw new Error("Table S6 row has no matrix mapping: " + row[0]);
    const st = ecCell(rxn, "Stirred batch"), tg = ecCell(rxn, "ANEC flow cell");
    const out = row.slice();
    out[1] = kSI(kOf(rxn));
    out[3] = fxk(st.xk);
    out[4] = fcur(st.t0) + " → " + fcur(st.ec);
    out[5] = fcur(tg.t0) + " → " + fcur(tg.ec);
    out[6] = s6Limiter(rxn, kOf(rxn));
    // the intensification gain the main text quotes per row (Section 4, "1.1-fold to 24-fold"): unstirred -> rotating cylinder
    const un = ecCell(rxn, "Unstirred batch"), rc = ecCell(rxn, "Rotating cylinder 3000 rpm"), g = rc.ec / un.ec;
    // endpoints are printed to whatever precision makes their own ratio round to the printed gain
    const fg = (x) => x >= 10 ? x.toFixed(0) : x.toFixed(1);
    const gs = fg(g);
    let pu = null, pr = null;
    for (const sig of [0, 3, 4]) {
      const fend = (v) => sig ? v.toPrecision(sig) : (v < 1 ? v.toPrecision(2) : fcur(v));
      if (fg(parseFloat(fend(rc.ec)) / parseFloat(fend(un.ec))) === gs) { pu = fend(un.ec); pr = fend(rc.ec); break; }
    }
    if (pu === null) throw new Error("Table S6 gain column: no printed precision reproduces the gain for " + rxn);
    out[7] = pu + " \u2192 " + pr + " (\u00d7" + gs + ")";
    return out;
  });
}
const ARCH = [["Unstirred batch", "natural"], ["Stirred batch", "stirred"],
              ["Recirculating flow cell", "flow"], ["ANEC flow cell", "anec"],
              ["Microfluidic cell (25 \u03bcm gap)", "micro"],
              ["RDE 1600 rpm", "rde"], ["Rotating cylinder 3000 rpm", "rce"]];
const N_CELLS = 50 * ARCH.length;            // 350: the published matrix, seven archetypes
// THE ORDERING CLAIM (2026-09-07). With seven archetypes the medians of the three thin-film cells
// (microfluidic, RDE, rotating cylinder) lie within ~20 % of one another and are not claimed to be
// ordered; the claim is the four-step chain through the ANEC cell, with every thin-film archetype
// above it. Asserted here so the sentences below cannot outlive the matrix that licenses them.
const ORDER_CHAIN = ["natural", "stirred", "flow", "anec"], ORDER_THIN = ["micro", "rde", "rce"];
const ORDERING_TEXT = "unstirred < stirred < recirculating flow < ANEC, with the microfluidic, RDE and rotating-cylinder medians all above ANEC";
const MS = new Map(ARCH.map(([, k]) => [k, matStats(k)]));
(() => {
  const m = (k) => MS.get(k).median;
  const chainOK = ORDER_CHAIN.every((k, i) => i === 0 || m(ORDER_CHAIN[i - 1]) < m(k));
  const thinOK = ORDER_THIN.every(k => m(k) > m("anec"));
  if (!chainOK || !thinOK) throw new Error("the architecture-ordering claim (" + ORDERING_TEXT + ") does not hold on the matrix: " +
      ARCH.map(([, k]) => k + " " + m(k).toFixed(2)).join(", "));
})();
// >=100 mA cm-2 is quoted as a whole number, below that to one decimal -- the convention the
// manuscript already uses ("6, 17, 19, 49, 108 and 122").
const med  = (k) => { const m = MS.get(k).median; return m >= 100 ? String(Math.round(m)) : m.toFixed(1); };
const medI = (k) => String(Math.round(MS.get(k).median));
const ge25 = (k) => MS.get(k).ge25 + "/" + MS.get(k).n;
const ge50 = (k) => MS.get(k).ge50 + "/" + MS.get(k).n;
// ---- which rows clear 25 mA cm-2 in NO architecture, by carrier class, from the published matrix.
// Every sentence that names "the exceptions" reads this, and each named set is asserted, so a row that
// crosses the threshold fails the build instead of leaving a description behind.
const matCell = (name, key) => { const r = MROW.find(x => x[mcol("reaction")] === name);
  if (!r) throw new Error("tier0_ec_matrix.csv has no row " + name); return Number(r[mcol(key)]); };
const CLASS_OF = new Map(rxRows.map(r => [r[2], r[3]]));
// Figure 5b's y-axis stops at the limit make_figs_sec34.py sets; the cells above it are not drawn, so S11 names them
// (chemistry audit pass 7). The limit is read from the generator, the cells from the published matrix.
// a row name opens with a common noun ("Acrylonitrile hydrodimerization") or a name ("Shono ..."); only the first is lowercased
const ROW_PROPER = new Set(["Shono", "Kolbe", "Hofmann", "Wacker", "Giese", "Minisci", "Birch", "Ritter", "Appel", "Hofer", "Ni", "Co", "Cu", "Mn", "Rh", "Pd", "BQ", "ACT", "NHPI", "HMF", "TEMPO"]);
const lcRow = (rx) => { const w = rx.split(/[ -]/)[0]; return ROW_PROPER.has(w) || !/^[A-Z][a-z]+$/.test(w) ? rx : rx.charAt(0).toLowerCase() + rx.slice(1); };
// chemistry audit pass 7: the thioether is substrate-limited in its batch films (current at its planar cap), so "neither
// row responds to the reactor" was true of the Giese row only. The shape of each row is read from the matrix and asserted.
// the largest gain on a row's best-of-seven ceiling at the top of the declared k band (julia/catalyst_ec_sweep.csv)
const CK_BEST = (() => {
  const L = fs.readFileSync(path.join(__dirname, "julia", "catalyst_ec_sweep.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);
  const h = L[0], ri = h.indexOf("reaction"), ki = h.indexOf("k_M"), ii = h.indexOf("i_ec_mAcm2"); const best = new Map();
  for (const r of L.slice(1)) { const k = Number(r[ki]); if (k !== 0 && k !== 1e4) continue;
    const m = best.get(r[ri]) || {}; m[k] = Math.max(m[k] || 0, Number(r[ii])); best.set(r[ri], m); }
  let top = null; for (const [rx, m] of best) { const g = m[1e4] / m[0]; if (!top || g > top.gain) top = { rx, gain: g }; }
  const NAME = { "Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)": "the Ni-catalyzed cross-electrophile coupling",
    "Rh-catalyzed electrooxidative C-H alkenylation": "the Rh-catalyzed C–H alkenylation", "Ni-catalyzed aryl amination (ArBr + amine)": "the Ni-catalyzed aryl amination" };
  if (!NAME[top.rx]) throw new Error("CK_BEST: no display name for " + top.rx);
  return { row: NAME[top.rx], gain: top.gain }; })();
// SI S9 intro (chemistry audit pass 7): the h_int effect per architecture and the tightest margins, both computed
const hintSentence = () => {
  const E = BOUNDS.h_int_effect, F = BOUNDS.h_int_flips; if (!E || !F) throw new Error("si_sensitivity_bounds.json lacks the h_int sweep");
  const grp = (names) => { const v = names.map(n => { if (!E[n]) throw new Error("h_int_effect: no " + n); return E[n]; });
    const lo = Math.min(...v.map(x => x.low_pct[0])), hi = Math.max(...v.map(x => x.high_pct[1]));
    return lo.toFixed(0) + " to +" + hi.toFixed(hi < 1 ? 1 : 0) + "%"; };
  return "the unstirred beaker's boil-off ceilings by " + grp(["unstirred batch"]) + ", those of the stirred, recirculating and rotating cells by " +
    grp(["stirred batch", "recirculating flow", "RDE 1600 rpm", "rotating cyl. 3000 rpm"]) + " and those of the microfluidic chip and the stack by " +
    grp(["microfluidic 25 $\\mu$m", "zero-gap PEM stack"]) + (F.length ? ", reversing " + F.map(f => f[1] + " in the " + f[0]).join(", ") : ", and reverses no boil-off verdict (the liquid-cooling verdicts of §S6.2 do depend on it, Table S7i)");
};
// chemistry audit pass 8: the cylinder's MeCN margin (0.64) sat outside a THF..DMF range; take the range over all three
const ORG_RANGE = (a) => { const v = ["THF", "MeCN", "DMF"].map(x => T_MARG(x, a)); return f2(Math.min(...v)) + "–" + f2(Math.max(...v)); };
// chemistry audit pass 8: the load-bearing list is the ledger's conditional tier (results/assumption_ledger.json), not typed
const LB_COOLERS = "the declared wall thickness and gap of the water jacket, whose thin ends decide whether THF at the rotating cylinder can be cooled (Table S7i)";
// derived rows that flag a conditionality, read from the registry rather than typed (it had said "one derived value")
const LB_DERIVED_NAMES = { "0.2 M NaI/DMF": "the DMF conductivity (Table S7f)", "Vessel external area": "the declared vessel diameter behind the beaker's σ (Table S7i)",
  "Liquid cooling: water jacket (forced-flow vessel cells)": "the water-jacket construction (Table S7i)",
  "Liquid cooling: cooled plate (stack and chip)": "the cooled-plate construction (Table S7i)",
  "Inter-electrode gap (rotating cylinder)": "the rotating cylinder's inter-electrode gap (Table S7i)" };
const LB_DERIVED_TXT = () => {
  const flagged = ALLROWS.filter(r => r[pcol("provenance_class")] === "derived" && r[pcol("sensitivity")].split(/(?<=\.)\s+/)
    .some(sen => /\bconditional\b/i.test(sen) && !/\b(no|not|none|never|without|unconditional)\b/i.test(sen)))
    .map(r => r[pcol("parameter")]);
  const miss = flagged.filter(n => !LB_DERIVED_NAMES[n]);
  if (miss.length) throw new Error("load-bearing sentence: no display name for derived row(s) " + miss.join("; "));
  return numWordCap(flagged.length).toLowerCase() + " derived " + (flagged.length === 1 ? "value carries" : "values carry") + " the same flag: " + listAnd(flagged.map(n => LB_DERIVED_NAMES[n]));
};
const LB_FILMS = "the internal film coefficients of the forced-flow cells and the stack, which sit in series inside their coolers (Table S7i)";
const LB_TEMP = "the ambient and coolant temperature (Table S7i)";
const LB_NAMES = {
  "HFIP: phi (assoc.)": "the HFIP association factor (Table S7b)",
  "Br- (1:1 H2O/MeCN, bromination row)": "the bromide diffusivity of the bromination row (Table S7d)",
  "Br2 (MeCN)": "the bromine diffusivity of the Hofmann and amidyl rows (Table S7d)",
  "Pyridinium pyH+ (acetone, NHPI row)": "the pyridinium diffusivity of the NHPI row (Table S7d)",
  "n_carrier (electrons per carrier turnover)": "the electrons per carrier turnover (Table S7e)",
  "3.0 M LiBr/THF": "the THF conductivity (Table S7f)",
  "Inter-electrode gap (beaker)": "the beaker inter-electrode gap that the rotating disc inherits (Table S7i)",
  "Inter-electrode gap (zero-gap PEM stack)": "the zero-gap stack's declared gap (Table S7i)",
  "i_design (zero-gap PEM stack)": "the zero-gap stack's declared current density (Table S7i)",
  "Cell volume / electrode area": "the declared 100 mL charge, which sets the beaker σ that the rotating cells take (Table S7i)",
  "Free-convection operating point (unstirred batch)": "the free-convection operating point of the unstirred batch cell (Table S7g)",
  "RDE operating point": "the rotation rate of the rotating disc (Table S7g)",
  "RCE operating point": "the rotation rate of the rotating cylinder (Table S7g)",
  "sigma (recirculating flow, RDE, rotating cylinder)": "the surface-area ratio σ that the recirculating cell and the two rotating electrodes inherit from the beaker (Table S7i)",
  "Ea (kappa(T) Arrhenius upper bound, S6.3)": "the activation energy of κ(T) (Table S7i)",
  "Vessel wall thickness (jacketed cell)": LB_COOLERS, "Cooling-jacket gap": LB_COOLERS, "Cooled-plate thickness": LB_COOLERS,
  "Cooled-plate channel D_h": LB_COOLERS, "Cooled-plate rib area factor": LB_COOLERS,
  "h_int (forced flow, centimetre gap)": LB_FILMS, "h_int (forced flow, thin gap)": LB_FILMS,
  "T_amb (§S6)": LB_TEMP, "Coolant inlet temperature (liquid cooling)": LB_TEMP };
const loadBearingSentence = () => {
  const led = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "assumption_ledger.json"), "utf8"));
  const t3 = led.rows.filter(r => r.tier === "T3").map(r => r.parameter);
  const miss = t3.filter(n => !LB_NAMES[n]);
  if (miss.length) throw new Error("load-bearing sentence: no display name for ledger row(s) " + miss.join("; "));
  return "What is left load-bearing is the " + numWord(t3.length) + " assumption rows whose sensitivity column states a conclusion that turns inside the tested range: "
    + listAnd([...new Set(t3.map(n => LB_NAMES[n]))]) + "; " + LB_DERIVED_TXT() + ".";
};
const tightestSentence = () => {
  const prep = T_ARCH.filter(a => !/zero-gap/.test(a)), rce = "rotating cyl. 3000 rpm";
  for (const sol of ["THF", "MeCN", "DMF"]) { const m = prep.map(a => [a, T_MARG(sol, a)]).sort((x, y) => x[1] - y[1])[0];
    if (m[0] !== rce) throw new Error("tightestSentence: the tightest " + sol + " margin is at " + m[0]); }
  return "Among the six preparative architectures the tightest thermal margins fall at the rotating cylinder, which has the highest transport ceiling and a " +
    (100 * T_GAP[rce]).toFixed(1) + " cm ohmic path: " + f2(T_MARG("THF", rce)) + "× for THF, " + f2(T_MARG("MeCN", rce)) + "× for MeCN and " +
    f2(T_MARG("DMF", rce)) + "× for DMF, with only the aqueous reference clearing at " + f2(T_MARG("aq. NaOH", rce)) + "×; the zero-gap stack, run at a declared reference current, falls shorter still (§S6.1).";
};
const thioGieseShape = () => {
  const order = ["Unstirred batch", "Stirred batch", "Recirculating flow cell", "ANEC flow cell", "Microfluidic cell (25 um gap)", "RDE 1600 rpm", "Rotating cylinder 3000 rpm"];
  const cell = (frag, r) => EC.find(c => c.rxn.includes(frag) && (c.reactor === r || (r.startsWith("Microfluidic") && c.reactor.startsWith("Microfluidic"))));
  const gi = order.map(r => cell("Giese", r)), th = order.map(r => cell("Thioether", r));
  if (gi.some(c => !c) || th.some(c => !c)) throw new Error("thioGieseShape: missing cells");
  const gSpread = Math.max(...gi.map(c => c.ec)) / Math.min(...gi.map(c => c.ec));
  const capped = th.filter(c => c.ec >= c.cap && c.cap > c.t0).map(c => c.reactor);
  const peak = th.reduce((a, b) => (b.ec > a.ec ? b : a)).reactor;
  const thin = th.slice(4), thinR = thin.map(c => c.ec / c.sav);
  if (!(gSpread < 1.25) || capped.join() !== "Unstirred batch,Stirred batch" || peak !== "ANEC flow cell" || thinR.some(v => v < 0.9 || v > 1.25))
    throw new Error("thioGieseShape: the sentence no longer describes the matrix (" + [gSpread, capped, peak, thinR].join(" | ") + ")");
  return "the Giese current changes by less than " + Math.ceil(100 * (gSpread - 1)) + "% across the seven films, while the thioether's follows substrate supply in the two batch films (at its planar cap), peaks on the ANEC film and lies within " + Math.ceil(100 * (Math.max(...thinR) - 1)) + "% of its kinetic plateau in the three thin films.";
};
const fig5Clip = () => {
  const src = fs.readFileSync(path.join(__dirname, "figs", "make_figs_sec34.py"), "utf8");
  const m = /d\.set_yscale\("log"\); d\.set_ylim\(([0-9.eE+-]+),\s*([0-9.eE+-]+)\)/.exec(src);
  if (!m) throw new Error("Figure 5b: no y-limit found in figs/make_figs_sec34.py");
  const top = Number(m[2]), word = { natural: "unstirred", stirred: "stirred", flow: "recirculating flow", anec: "ANEC",
    micro: "microfluidic", rde: "RDE", rce: "rotating-cylinder" };
  const by = [];
  for (const r of MROW) {
    const hit = Object.keys(word).filter(k => Number(r[mcol(k)]) > top);
    if (hit.length) by.push([r[mcol("reaction")], hit]);
  }
  const n = by.reduce((a, b) => a + b[1].length, 0);
  return { top, n, text: n ? numWordCap(n) + " of the " + MROW.length * Object.keys(word).length + " cells lie above the panel's " +
    top.toLocaleString("en-US") + " mA cm⁻² axis limit and are not drawn: " +
    listAnd(by.map(([rx, ks]) => lcRow(rx) + " in the " + listAnd(ks.map(k => word[k])) + " cell" + (ks.length > 1 ? "s" : ""))) + "." : "" };
};
const CARR_mM = new Map(rxRows.map(r => [r[2], 1000 * Number(r[7])]));
const rowBest = (name) => Math.max(...ARCH.map(([, k]) => matCell(name, k)));
const NEVER25 = (cls) => rxRows.map(r => r[2]).filter(n => CLASS_OF.get(n) === cls && rowBest(n) < 25);
const sameSet = (a, b) => a.length === b.length && a.every(x => b.includes(x));
const DIR_NEVER = NEVER25("substrate"), MED_NEVER = NEVER25("mediator"), CAT_NEVER = NEVER25("catalyst");
if (!sameSet(DIR_NEVER, ["Benzaldehyde -> benzyl alcohol", "Radical-cation Diels-Alder (catalytic in e-)"]))
  throw new Error("the substrate-carried rows below 25 mA cm-2 everywhere are no longer the two the text names: " + JSON.stringify(DIR_NEVER));
if (!sameSet(MED_NEVER, ["ACT-mediated alcohol oxidation (flow, hectogram)", "Cathodic Giese (R-I + alkene)", "Oxazole synthesis from ketones and acetonitrile"]))
  throw new Error("the mediated rows below 25 mA cm-2 everywhere are no longer the three the text names: " + JSON.stringify(MED_NEVER));
const CAT_CLEAR = rxRows.map(r => r[2]).filter(n => CLASS_OF.get(n) === "catalyst" && rowBest(n) >= 25);
if (!sameSet(CAT_CLEAR, ["Cathodic Ni aryl-aryl homocoupling"]))
  throw new Error("the catalyst rows clearing 25 mA cm-2 are no longer the one the text names: " + JSON.stringify(CAT_CLEAR));
const mMfmt = (v) => v >= 10 ? String(Math.round(v)) : v.toFixed(1);
const CAT_NEVER_mM = mMfmt(Math.min(...CAT_NEVER.map(n => CARR_mM.get(n)))) + "–" + mMfmt(Math.max(...CAT_NEVER.map(n => CARR_mM.get(n))));
const CAT_CLEAR_mM = mMfmt(CARR_mM.get(CAT_CLEAR[0]));
const N_NEVER25 = DIR_NEVER.length + MED_NEVER.length + CAT_NEVER.length;
const ACT_TOP = Math.round(rowBest("ACT-mediated alcohol oxidation (flow, hectogram)"));
// ---- chain rows (Table S10): solved and tabulated, counted in every all-fifty statistic, left out of CLASS medians.
const CHAIN_ROWS = STOR.filter(r => r[stoc("kind")] === "chain").map(r => r[stoc("reaction")]);
if (!sameSet(CHAIN_ROWS, ["Radical-cation Diels-Alder (catalytic in e-)", "Co-H alkene isomerization (catalytic)"]))
  throw new Error("the chain rows are no longer the two the text names: " + JSON.stringify(CHAIN_ROWS));
if (CHAIN_ROWS.some(n => rowBest(n) >= 25)) throw new Error("a chain row clears 25 mA cm-2; the all-fifty counts would then depend on a charge-normalised row");
const classMedian = (cls, k, chains) => { const v = rxRows.map(r => r[2]).filter(n => CLASS_OF.get(n) === cls && (chains || !CHAIN_ROWS.includes(n))).map(n => matCell(n, k)).sort((a, b) => a - b);
  const m = v.length; return m % 2 ? v[(m - 1) / 2] : 0.5 * (v[m / 2 - 1] + v[m / 2]); };
const allMedianWithout = (k, drop) => { const v = rxRows.map(r => r[2]).filter(n => !drop.includes(n)).map(n => matCell(n, k)).sort((a, b) => a - b);
  const m = v.length; return m % 2 ? v[(m - 1) / 2] : 0.5 * (v[m / 2 - 1] + v[m / 2]); };
const CHAIN_MEDIAN_SHIFT = Math.max(...ARCH.map(([, k]) => Math.abs(allMedianWithout(k, CHAIN_ROWS) / MS.get(k).median - 1)));
// The charge each chain row carries is read from the reaction table; it had been typed, and the isomerization's stayed at
// the bottom of its paper's general range (0.5) after the row moved to compound 17's own 3 F/mol.
// the concentration range of the rows whose exemplar runs at a 0.2 mmol scale, read from the reaction table (it was typed
// "0.03-0.17 M", which mixed in the 0.5 mmol entries)
// chemistry audit pass 7: a row runs at a 0.2 mmol scale when its LIMITING reagent is 0.2 mmol over the stated volume
// ("(0.2 mmol/3.9 mL)", "on 0.2 mmol scale"); a bare "0.2 mmol" also matched row 1's excess aryl bromide (a 0.1 mmol run)
// and row 11's "half the 0.2 mmol of the general procedure"
const MMOL02 = (() => { const v = csv.slice(1).map(splitCSV).filter(r => /\(0\.20? mmol ?\/|on 0\.2 mmol scale/.test(r[col("conc_provenance")])).map(r => Number(r[col("C_substrate_M")]));
  if (v.length < 5) throw new Error("expected the 0.2 mmol-scale rows, found " + v.length);
  const f = (x) => x < 0.1 ? x.toFixed(3).replace(/0$/, "") : x.toFixed(2); return f(Math.min(...v)) + "–" + f(Math.max(...v)); })();
// the S8 diffusivity census, read from the reaction table's D_provenance column (it was typed "34 Wilke-Chang, 11 Stokes-
// Einstein, 5 Nernst-Einstein" and went stale as rows were re-sourced)
const DPROV = (() => { const v = csv.slice(1).map(splitCSV).map(r => r[col("D_provenance")]);
  const o = { wc: v.filter(x => x.startsWith("Wilke-Chang")).length, se: v.filter(x => x.startsWith("Stokes-Einstein")).length,
              ne: v.filter(x => /Nernst-Einstein/.test(x)).length, walden: v.filter(x => x.startsWith("Walden")).length,
              meas: v.filter(x => x.startsWith("measured")).length };
  if (o.wc + o.se + o.ne + o.meas !== 50) throw new Error("D_provenance census does not cover the fifty rows: " + JSON.stringify(o));
  if (o.meas !== 1 || !v.some(x => x.startsWith("measured") && /Cussler/.test(x))) throw new Error("the S8 census names one measured diffusivity (dissolved O2, Cussler); the table has " + o.meas);
  return o; })();
const N_SUB_OF = new Map(csv.slice(1).map(splitCSV).map(r => [r[col("reaction")], Number(r[col("n_substrate")])]));
const fpm = (n) => { const v = N_SUB_OF.get(n); if (!(v > 0)) throw new Error("no n_substrate for chain row " + n); return String(v); };
const chainSentence = () => "Two rows are chain processes whose electron count is the charge the exemplar passes — the radical-cation Diels–Alder at " + fpm("Radical-cation Diels-Alder (catalytic in e-)") + " F mol⁻¹ and the cobalt-hydride alkene isomerization at " + fpm("Co-H alkene isomerization (catalytic)") + " F mol⁻¹ (Table S10). Both are solved and tabulated like every other row and are counted in every fifty-row median and count; at the charge carried neither clears 25 mA cm⁻² in any architecture (Table S7 gives the first across its paper's own range of charge), and leaving both out moves no architecture median by more than " + (100 * CHAIN_MEDIAN_SHIFT).toFixed(0) + "%. Class medians are quoted over the rows that are stoichiometric in charge: the catalyst-class median runs from " + classMedian("catalyst", "natural", false).toFixed(2) + " to " + classMedian("catalyst", "rce", false).toFixed(1) + " mA cm⁻² (unstirred to rotating cylinder) over those " + numWord(N_CAT - 1) + " rows and from " + classMedian("catalyst", "natural", true).toFixed(2) + " to " + classMedian("catalyst", "rce", true).toFixed(1) + " with the isomerization included.";

const pcsv = fs.readFileSync(PROV_CSV, "utf8").replace(/\r/g, "").trim().split("\n");
const phdr = splitCSV(pcsv[0]);
const pcol = (n) => phdr.indexOf(n);
let prows = pcsv.slice(1).map(splitCSV);
// ---- PUBLISHED SUBSET -------------------------------------------------------------------
// The SI prints the parameters a reader needs in order to check a claim, not the ones that exist
// only because the model was built incrementally. data/registry_liveness.py applies a stated rule
// (a row is dead if its solvent is used by no reaction, or its own registry text declares it
// display-only) and writes the two lists. Filtering here rather than in the registry keeps
// parameters_provenance.csv complete as the internal record and as the provenance file for the
// code, while the published appendix carries only load-bearing rows.
//
// This is a disclosed omission, not a silent one: the count and the reason are stated in §S9.
const LIVENESS = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "registry_liveness.json"), "utf8"));
const DEAD = new Set(LIVENESS.dead_parameters);
const N_OMITTED = LIVENESS.n_dead;
if (LIVENESS.n_total !== prows.length) {
  throw new Error("registry_liveness.json describes " + LIVENESS.n_total + " rows but the "
                  + "registry has " + prows.length + "; re-run data/registry_liveness.py");
}
const ALLROWS = prows;                       // the complete internal record, before the trim
// ---------- Table S3: exactly the solvents the fifty rows use ----------
// Built from solvents.csv for every solvent key reactions_50.csv names, each checked against its registry rows in
// Table S7b (M, mu, rho, phi must agree), so the table can neither omit a solvent a row uses nor print one none uses.
const RX_SOLV_I = hdr.indexOf("solvent");
if (RX_SOLV_I < 0) throw new Error("reactions_50.csv has no solvent column");
const S3_KEYS = [...new Set(csv.slice(1).map(splitCSV).map(r => r[RX_SOLV_I]))];
const S3_REG = (lab, q) => ALLROWS.find(r => r[pcol("parameter")] === lab + ": " + q);
function s3Label(key) {
  if (S3_REG(key, "mu (25 C)")) return key;
  if (key.includes(":")) { if (S3_REG(key + " v/v", "mu (25 C)")) return key + " v/v"; throw new Error("no registry row for solvent " + key); }
  const keyed = new Set(SOLV_CSV.map(r => r[0]).filter(k => k.startsWith(key + " ")).map(k => k + " v/v"));
  const c = [...new Set(ALLROWS.map(r => r[pcol("parameter")]).filter(p => p.startsWith(key + " ") && p.endsWith(": mu (25 C)"))
                          .map(p => p.slice(0, -": mu (25 C)".length)))].filter(l => !keyed.has(l));
  if (c.length !== 1) throw new Error("solvent " + key + " maps to " + c.length + " registry labels: " + c.join(" | "));
  return c[0];
}
const s3Src = (r) => { const st = r[pcol("provenance_class")], c = r[pcol("citation")];
  const short = /^CRC Handbook/.test(c) ? "CRC 97th ed." : /^Huber/.test(c) ? "IAPWS 2008" : /^Krumgalz/.test(c) ? "Krumgalz 1983"
    : /^Ansari/.test(c) ? "Ansari & Singh 2022" : /^Declared bracket/.test(c) ? "pure-component bracket" : /^CRC/.test(c) ? "CRC mixture table (20 °C)" : "no measured table";
  return st + "; " + short; };
const S3_ROWS = S3_KEYS.map(key => {
  const lab = s3Label(key), src = SOLV.get(key);
  if (!src) throw new Error("solvents.csv has no row " + key);
  const regv = { M: "M", mu: "mu (25 C)", rho: "rho", phi: "phi (assoc.)" };
  for (const [k, q] of Object.entries(regv)) {
    const rr = S3_REG(lab, q);
    if (!rr || Math.abs(parseFloat(rr[pcol("value")]) - parseFloat(src[k])) > 1e-9 * Math.max(1, Math.abs(parseFloat(src[k]))))
      throw new Error("Table S3: " + lab + " " + q + " registry " + (rr ? rr[pcol("value")] : "missing") + " vs solvents.csv " + src[k]);
  }
  const f = (v, d) => Number(v).toFixed(d);
  return [lab.replace(/H2O/g, "H₂O").replace(/MeNO2/g, "MeNO₂"), lab.includes("/") ? f(src.M, 2).replace(/0$/, "") : f(src.M, 2),
          f(src.mu, 3), f(src.rho, 3), String(Number(src.phi)), s3Src(S3_REG(lab, "mu (25 C)")), lab];
}).sort((x, y) => (x[6].includes("/") - y[6].includes("/")));
const S3_MIX = S3_ROWS.filter(r => r[6].includes("/"));
const S3_MIX_DERIVED = S3_MIX.filter(r => r[5].startsWith("derived")).map(r => r[0]).sort().reverse();
if (S3_MIX_DERIVED.join("|") !== "H₂O/MeCN 1:1 v/v") throw new Error("Table S3 caption describes one Ansari-derived mixture and the declared 2:1 viscosity; the registry now derives " + S3_MIX_DERIVED.join(", "));
// The 2:1 mixture: its density rounds to the Ansari & Singh interpolation, its viscosity does not, so only mu is declared.
// Every number in the caption's sentence is read from the registry row, never typed.
// The census clause names the mixture properties derived from a measured isotherm, read from the registry so it cannot
// drift from Table S3: the 1:1 viscosity and density and the 2:1 density (the 2:1 viscosity is a declared value).
const MIX_DERIVED_TXT = (() => {
  const got = ALLROWS.filter(r => r[pcol("category")].startsWith("2. ") && /\//.test(r[pcol("parameter")])
      && /: (mu \(25 C\)|rho)$/.test(r[pcol("parameter")]) && r[pcol("provenance_class")] !== "assumption").map(r => r[pcol("parameter")]).sort();
  const want = ["H2O/MeCN 1:1 v/v: mu (25 C)", "H2O/MeCN 1:1 v/v: rho", "H2O/MeCN 2:1 v/v: rho"];
  if (JSON.stringify(got) !== JSON.stringify(want)) throw new Error("census clause: the derived mixture properties are now " + got.join(", "));
  return "the viscosity and density of H₂O/MeCN 1:1 and the density of H₂O/MeCN 2:1, derived from a measured isotherm";
})();
const S3_21 = (() => {
  const mu = S3_REG("H2O/MeCN 2:1 v/v", "mu (25 C)"), rho = S3_REG("H2O/MeCN 2:1 v/v", "rho");
  if (mu[pcol("provenance_class")] !== "assumption" || rho[pcol("provenance_class")] !== "derived")
    throw new Error("Table S3 caption: the H2O/MeCN 2:1 states moved (mu " + mu[pcol("provenance_class")] + ", rho " + rho[pcol("provenance_class")] + ")");
  const m = /gives eta = ([0-9.]+) cP and rho = ([0-9.]+) g cm-3/.exec(mu[pcol("method_note")]);
  if (!m) throw new Error("Table S3 caption: the 2:1 interpolation is no longer stated in its registry row");
  const muC = parseFloat(mu[pcol("value")]), rhoC = parseFloat(rho[pcol("value")]);
  const pm = /the carried [0-9.]+ cP is ([0-9.]+) pct lower/.exec(mu[pcol("sensitivity")]);
  if (!pm) throw new Error("Table S3 caption: the 2:1 viscosity shortfall is no longer stated in its registry row");
  return {muI: m[1], rhoI: m[2], muC: muC.toFixed(2), rhoC: rhoC.toFixed(2), pct: pm[1]};
})();
const S3_RHO_ASSUMED = S3_ROWS.filter(r => !r[6].includes("/") && S3_REG(r[6], "rho")[pcol("provenance_class")] === "assumption").map(r => r[0]);
S3_ROWS.forEach(r => r.length = 6);
const S3_ROWS_SRC = S3_ROWS.map(r => r[5]);
// S3.1: the declared supporting-ion slots, read from the ion table the solver uses (a slot is a class default only when it IS
// the default; apply_ion_diffusivities.py labels the rest "DECLARED VALUE")
const SLOT_BASIS = (() => { const L = fs.readFileSync(path.join(DATA, "electrolyte_ions.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV), h = L[0];
  return L.slice(1).flatMap(r => [r[h.indexOf("D_cat_basis")], r[h.indexOf("D_an_basis")]]); })();
const SLOT_DEF = SLOT_BASIS.filter(b => /^DECLARED CLASS DEFAULT/.test(b)).length, SLOT_VAL = SLOT_BASIS.filter(b => /^DECLARED VALUE/.test(b)).length;
if (SLOT_DEF + SLOT_VAL !== JSON.parse(fs.readFileSync(path.join(__dirname, "results", "unsourced_D_sensitivity.json"), "utf8")).n_slots)
  throw new Error("S3.1: the declared slots in electrolyte_ions.csv do not match the G-DSENS sweep; re-run data/sensitivity_unsourced_D.py");
prows = prows.filter(r => !DEAD.has(r[pcol("parameter")]));
// Table S7's blocks are lettered (a), (b), ... in THIS order, and the SI cites them by letter
// ("Table S7g" for the stirred-batch delta band, "Table S7i" for sigma and the design currents).
// Taken in CSV first-appearance order the categories run 1,2,3,4,5,6,9,7,8,10,11 -- category 9
// sits between 6 and 7 -- so every letter after (f) shifted and two citations pointed at the
// wrong block: delta lives in "7. Reactors" which was lettered (h), while (g) was "9. Thermal
// model". Sorting by the leading category number restores the order the prose was written
// against, and makes S7c/S7d/S7f/S7g/S7i all correct. G-GHOST asserts the mapping.
const pcats = [...new Set(prows.map(r => r[pcol("category")]))]
  .sort((x, y) => (parseInt(x, 10) || 0) - (parseInt(y, 10) || 0));
function census(filter) {
  const rs = filter ? prows.filter(filter) : prows;
  const c = { n: rs.length, measured: 0, derived: 0, assumption: 0 };
  rs.forEach(r => { c[r[pcol("provenance_class")]]++; });
  return c;
}
const CAT = (frag) => (r) => r[pcol("category")].includes(frag);
// Number agreement for the templated censuses. Without it the counts, which are computed, land
// inside prose that was written when they were larger: "1 are derived and 1 are assumptions",
// "seven of those 1". A census that is right and reads as broken is not better than a wrong one.
const isAre = (n) => (n === 1 ? "is" : "are");
const nOf = (n, sing, plur) => n + " " + (n === 1 ? sing : (plur || sing + "s"));
const CENSUS_ALL  = census();
const CENSUS_COND = census(CAT("Electrolyte conductivities"));
const CENSUS_DIFF = census(CAT("Solver species diffusivities"));
// Census over EVERY row, trimmed or not. The sentence in S9 that contrasts the two sets used to
// TYPE this one ("0 measured, 8 derived and 41 assumption") while computing the other, so when
// three conductivities became measured the contrast sentence kept asserting a data gap the
// tables on the facing page had already partly closed. Nothing about a census may be typed.
function censusAll(filter) {
  const rs = filter ? ALLROWS.filter(filter) : ALLROWS;
  const c = { n: rs.length, measured: 0, derived: 0, assumption: 0 };
  rs.forEach(r => { c[r[pcol("provenance_class")]]++; });
  return c;
}
const CENSUS_COND_ALL = censusAll(CAT("Electrolyte conductivities"));
// The four conductivities that carry a §S6 conclusion; the rest of category 6 is display-only
// because kappa enters no transport quantity (see the Table S4 caption).
const N_COND_CONCLUSION = 4;
// The assumption LEDGER (figs/analysis_assumption_ledger.py -> results/assumption_ledger.json).
// A bare "N assumption" invites the reading that N numbers were invented. The ledger sorts every
// state-C row by what actually backs it, and these counts are read from its output rather than
// typed, so the prose cannot drift from the classifier. If the file is absent the sentence is
// omitted entirely rather than falling back to a stale literal.
// ---- SI sensitivity bounds (results/si_sensitivity_bounds.json) --------------------------------
// Generated by data/si_sensitivity_bounds.py and gated by data/check_si_bounds.py (G-SIBOUNDS),
// which asserts that every value lies inside its own bounds AND that every number G-MSDERIVED
// checks against the manuscript is either bounded here or exempt with a stated reason. Loaded
// rather than typed so the section cannot drift from the model it describes.
const BOUNDS = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "si_sensitivity_bounds.json"), "utf8"));

// ---- S10: the largest change in catalytic amplification between the two delta limits of one architecture
const BANDAMP = (() => { const rd = (f) => fs.readFileSync(path.join(__dirname, "julia", f), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);
  const amp = (f, med) => { const L = rd(f), h = L[0], m = new Map();
    L.slice(1).forEach(r => m.set(r[0] + "|" + r[1] + (med ? "" : "|" + r[h.indexOf("k_M")]),
      med ? Number(r[h.indexOf("amplification")]) : Number(r[h.indexOf("i_ec_mAcm2")]) / Number(r[h.indexOf("i_fick_mAcm2")])));
    return m; };
  let best = 1, n = 0;
  for (const med of [true, false]) {
    const lo = amp(med ? "mediated_ec_matrix_band_lo.csv" : "catalyst_ec_band_lo.csv", med), hi = amp(med ? "mediated_ec_matrix_band_hi.csv" : "catalyst_ec_band_hi.csv", med);
    for (const [k, a] of lo) if (hi.has(k)) { n++; best = Math.max(best, a / hi.get(k), hi.get(k) / a); } }
  if (n < 50) throw new Error("S10: the band-edge files pair only " + n + " cells");
  return best; })();
// ---- S10: whether the four-step ordering holds at the limits of the transport bands, not only at the centre
const ORD_NAME = { natural: "unstirred", stirred: "stirred", flow: "recirculating-flow", anec: "ANEC" };
const BM = (k, w) => BOUNDS.transport["median, " + k][w];
const ORD_BREAK = ["natural", "stirred", "flow", "anec"].slice(1).map((k, i, a) => [["natural", "stirred", "flow", "anec"][i], k])
  .filter(([a, b]) => !(BM(a, "lower") < BM(b, "lower") && BM(a, "upper") < BM(b, "upper")));
// ---- S10: the unstirred film band the bounds solve uses (julia/delta_bounds.csv), checked against the free-convection
// envelope it is taken from (results/free_convection_delta.json, at the extreme rows of the set)
const DB_NAT = (() => { const L = fs.readFileSync(path.join(__dirname, "julia", "delta_bounds.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV), h = L[0];
  const r = L.slice(1).filter(x => x[h.indexOf("reactor")] === "Unstirred batch");
  const lo = [...new Set(r.map(x => Number(x[h.indexOf("delta_lo_um")])))], hi = [...new Set(r.map(x => Number(x[h.indexOf("delta_hi_um")])))];
  if (lo.length !== 1 || hi.length !== 1) throw new Error("S10: the unstirred band is not one value per edge in delta_bounds.csv");
  const fc = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "free_convection_delta.json"), "utf8"));
  if (Math.abs(lo[0] / fc.delta_band_lo_um - 1) > 0.01 || Math.abs(hi[0] / fc.delta_band_hi_um - 1) > 0.01) throw new Error("S10: the unstirred band of the bounds solve is not the free-convection envelope");
  return [lo[0], hi[0]]; })();
// ---- S11: the declared case behind Figures 4c and 5a, read from the solver that draws them
const PROFILE_CASE = (() => { const src = fs.readFileSync(path.join(__dirname, "julia", "run_profiles.jl"), "utf8");
  for (const w of ["const C_S  = 500.0", "const D_S  = 1.0e-9", 'Species("S",  0.0, D_S,'])
    if (!src.includes(w)) throw new Error("run_profiles.jl no longer reads " + w + "; the Figure 4c/5a notes describe that case");
  return "a declared case (0.5 M neutral substrate, one electron, D = 1 × 10⁻⁹ m² s⁻¹)"; })();

// ---- kappa(T) bracket (results/figK_kappaT_sensitivity.json) ----------------------------------
// The MeCN/microfluidic reversal used to be TYPED into S6.3 as "440 ... and 563". The boiling
// points moved to their CRC values on 2026-08-30 and those two literals did not, so S6.3 printed
// 440 while S6.1, three paragraphs earlier, printed the corrected 438 FOR THE SAME QUANTITY --
// the document disagreed with itself. Both ends are computed here now (trap 10: never type an
// expectation you could derive), and figs/analysis_kappaT_sensitivity.py (G-KAPPAT) parses the
// finished sentence back out of the .docx and re-checks it against the model.
// ---- reactor-engineering quantities (results/reactor_engineering.json) -----------------------
// A limiting current density is a FLUX. S8.1 reports the productivity quantities it cannot
// express, computed from the SAME channel geometry the Leveque correlation uses.
const RE = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "reactor_engineering.json"), "utf8"));
const reA = RE.channels[0], reB = RE.channels[1], reR = RE.ratios;

// ---- what the dataset can say about operating current density (Jonas Rein's "(<XX mA cm-2)")
// results/dataset_current_density.json, from data/dataset_current_density.py
const DJ = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "dataset_current_density.json"), "utf8"));
if (DJ.verdict !== "PASS") throw new Error("dataset_current_density.json is not PASS");

// ---- dilute-theory stratification (results/dilute_theory_stratify.json) ----------------------
// S1.1 (i) already declares that above ~1 M the constant-mobility assumption is quantitatively
// wrong. The reviewer's NEXT question is the one a declaration does not answer: how much of the
// headline count comes from exactly those rows? Computed, never typed.
const DS = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "dilute_theory_stratify.json"), "utf8"));

// ---- EC' panel-boundary exposure (results/ecprime_panel_sensitivity.json) --------------------
// The two diffusivities of the S5.4 / §S5.4 base case are state-C declarations, and main-text Fig. 6d-f draws three real
// rows whose regime labels come from the solve; the gate states how far the boundaries move and whether the labels survive.
const EP = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "ecprime_panel_sensitivity.json"), "utf8"));

// ---- internal-film series bound (results/hint_series_bound.json) -----------------------------
const HB = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "hint_series_bound.json"), "utf8"));

// ---- Schmidt-range extrapolation of the RCE correlation (results/schmidt_extrapolation.json) --
const SX = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "schmidt_extrapolation.json"), "utf8"));
// ---- solution-viscosity sweep (data/sensitivity_solution_viscosity.py): which column moves first, and at what ratio
const SV = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "solution_viscosity_sensitivity.json"), "utf8"));
const SV_ARCH = ["unstirred", "stirred", "recirculating-flow", "ANEC", "microfluidic", "RDE", "rotating-cylinder"];
const svDiff = (r) => r.n25.map((n, i) => n !== SV.baseline_n25[i]);
const SV_FIRST = SV.sweep.find(r => svDiff(r).some(Boolean));
const SV_UNST = SV.sweep.find(r => r.n25[0] !== SV.baseline_n25[0]);
const SV_NEVER = SV_ARCH.filter((a, i) => SV.sweep.every(r => r.n25[i] === SV.baseline_n25[i]));
const SV_MAX = Math.max(...SV.sweep.map(r => r.factor));
if (!SV.sweep.every(r => r.ordering_holds)) throw new Error("the viscosity sweep breaks the architecture ordering; §S1.1 (ii) says it survives");
const SV_SENT = SV_FIRST ? "The first \u226525 mA cm\u207b\u00b2 count moves at \u03bc_solution/\u03bc_solvent = " + SV_FIRST.factor.toFixed(1) + ", in the "
  + listAnd(SV_ARCH.filter((a, i) => svDiff(SV_FIRST)[i]).map((a, i0) => { const i = SV_ARCH.indexOf(a); return a + " column (" + SV.baseline_n25[i] + " \u2192 " + SV_FIRST.n25[i] + " of 50)"; }))
  + (SV_UNST && SV_UNST !== SV_FIRST ? "; the unstirred count first moves at " + SV_UNST.factor.toFixed(1) + " (" + SV.baseline_n25[0] + " \u2192 " + SV_UNST.n25[0] + ")" : "")
  + "; the architecture ordering survives to " + SV_MAX.toFixed(1) + ", and the " + listAnd(SV_NEVER) + " counts do not move anywhere in that range."
  : "No \u226525 mA cm\u207b\u00b2 count moves up to \u03bc_solution/\u03bc_solvent = " + SV_MAX.toFixed(1) + ".";
// ---- cooling-class verdicts of S6.2 and the Bu4NPF6/THF example of S6.1 (data/thermal_conditional_flips.py)
const CF = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "thermal_conditional_flips.json"), "utf8"));
const CF_V = (sol, arch) => { const v = CF.verdicts.find(x => x.solvent === sol && x.architecture === arch); if (!v) throw new Error("thermal_conditional_flips.json lacks " + sol + " / " + arch); return v; };
const CF_THF_STACK = CF_V("THF", "zero-gap PEM stack");
if (!CF_THF_STACK.conditional || CF_THF_STACK.class !== "liquid cooling") throw new Error("the THF stack cooling class is no longer conditional liquid cooling; §S6.2 and Table S4 say it is");
// the 25 C conductivity band of an electrolyte, printed inline so the condensed SI (whose Table S4 omits it) carries it
const CF_BAND_TXT = (solv) => { const v = CF.verdicts.find(x => x.solvent === solv); const k = parseFloat(ELEC.get(v.electrolyte).kappa);
  const f = (x) => x >= 10 ? x.toFixed(0) : x.toFixed(1); return f(v.band_multiple[0] * k) + "\u2013" + f(v.band_multiple[1] * k) + " mS cm\u207b\u00b9"; };
const CF_THF_CM = ["unstirred batch", "stirred batch", "recirculating flow"].map(a => CF_V("THF", a));
const CF_PCT = (x) => (100 * x).toFixed(0);
const CF_ORG = CF.verdicts.filter(v => ["THF", "MeCN", "DMF"].includes(v.solvent));
const CF_CLASS_TXT = (c) => c;
// S6.2: the cheapest cooling class each architecture needs in the organic solvents, grouped by class
const CF_NEED = () => { const need = new Map();
  [...new Set(CF_ORG.filter(v => v.class !== "passive").map(v => v.architecture))].forEach(a => {
    const by = {}; CF_ORG.filter(v => v.architecture === a && v.class !== "passive").forEach(v => (by[v.class] = by[v.class] || []).push(v.solvent));
    const txt = Object.entries(by).map(([c, ss]) => CF_CLASS_TXT(c) + " in " + listAnd(ss)).join(" and ");
    need.set(txt, (need.get(txt) || []).concat([a])); });
  return [...need.entries()].map(([txt, as]) => "the " + listAnd(as.map(ARCH_SHORT)) + (as.length > 1 ? " each need " : " needs ") + txt); };
// 2026-10-06: liquid cooling as each architecture would be cooled (thermal_model.U_liquid via the CF json)
const CF_LIQ = (a) => CF.liquid_cooling[a];
const CF_LIQTXT = (a) => CF_LIQ(a).U_lo.toFixed(3) + "–" + CF_LIQ(a).U_hi.toFixed(3);
const CF_LIQ_NEED = CF_ORG.filter(v => v.class === "liquid cooling");
if (CF_LIQ_NEED.some(v => v.liquid_holds_across_construction === null)) throw new Error("liquid-cooling verdict without a construction flag");
const CF_MET = (v) => v.U_req <= v.U_liquid[1] ? "met within the declared construction range" : "beyond what the declared construction range can meet";   // 2026-10-07: one liquid class (author)
const CF_LIQ_ALL = CF.verdicts.filter(v => v.class === "liquid cooling");
const CF_THF_LIQ_TXT = () => { const v = CF_ORG.filter(x => x.solvent === "THF" && x.class === "liquid cooling" && x.flip_down_multiple !== null)
    .sort((a, b) => b.flip_down_multiple - a.flip_down_multiple);
  if (!v.length) throw new Error("no THF liquid-cooling verdict with a downward flip");
  return listAnd(v.map(x => xmul(x.flip_down_multiple, 2) + " (" + ARCH_SHORT(x.architecture) + ")")); };
const TAX = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "thermal_axis_sweeps.json"), "utf8"));
const TAX_MOVING = (key, only) => TAX[key].rows.filter(r => Object.keys(r.crossings).some(k => !only || only.includes(k)));
const TAX_LIQ = (arch) => TAX.inherited_sigma.rows.find(r => r.arch === arch && r.solvent === "THF").crossings.liquid_best;
// Where the activation terms of Eq. S18 carry the heat, at each cell's own operating current (pass 42, 2026-10-07: the sentence
// after Eq. S18 had put the stack with the chip, where activation dominates; in the stack it is 18-93 % by electrolyte).
const ASH = TAX.activation_share;
const TM_STACK_I = 1000;   // the zero-gap stack's declared current, mA cm-2 (thermal_model.REACTORS; Figure 7 caption)
const ASH_CM = ["unstirred batch", "stirred batch", "recirculating flow", "RDE 1600 rpm", "rotating cyl. 3000 rpm"];
const ASH_ORG = ["THF", "MeCN", "DMF"];
const ASH_VALS = (archs, solvs) => archs.flatMap(a => solvs.map(x => ASH[a][x]));
const ASH_ORG_OHM_MIN = 1 - Math.max(...ASH_VALS(ASH_CM, ASH_ORG));
const ASH_MICRO_MIN = Math.min(...ASH_VALS(["microfluidic 25 um"], ASH_ORG.concat(["aq. NaOH"])));
const ASH_STACK = ASH_VALS(["zero-gap PEM stack"], ASH_ORG.concat(["aq. NaOH"]));
const ASH_AQ = ASH_VALS(ASH_CM, ["aq. NaOH"]);
const PCT_RANGE = (v) => Math.floor(100 * Math.min(...v)) + "–" + Math.ceil(100 * Math.max(...v)) + " %";
const AX_I0 = TAX.axes.find(a => a.key === "i0");
if (!(ASH_ORG_OHM_MIN > 0.5)) throw new Error("the ohmic term no longer carries most of the heat in the organic centimetre-gap cells; the sentence after Eq. S18 says it does");
if (!(ASH_MICRO_MIN > 0.5)) throw new Error("the activation term no longer carries most of the heat in the microfluidic chip; the sentence after Eq. S18 says it does");
if (AX_I0.cells.some(c => c.changes && c.changes.length)) throw new Error("the i0 sweep now changes a cooling class; the sentence after Eq. S18 says it changes none");
const ASH_SENT = "at each cell's operating current (its median transport ceiling; the stack at " + (TM_STACK_I / 1000) + " A cm⁻²), in the three organic electrolytes at a centimetre gap the ohmic term carries at least " + Math.floor(100 * ASH_ORG_OHM_MIN) + " % of the heat; the activation terms carry " + Math.floor(100 * ASH_MICRO_MIN) + " % or more of it in the microfluidic chip, " + PCT_RANGE(ASH_STACK) + " in the stack and " + PCT_RANGE(ASH_AQ) + " in aqueous NaOH at a centimetre gap; and varying i₀ over " + AX_I0.x0 + "–" + AX_I0.x1 + " mA cm⁻² changes no cooling class in any cell, Table S12";
if (JSON.stringify(TAX_MOVING("stack_gap").map(r => r.solvent)) !== JSON.stringify(["THF"])
    || !TAX_MOVING("stack_current").some(r => r.solvent === "THF")
    || JSON.stringify(TAX_MOVING("inherited_sigma", ["liquid_any", "liquid_best"]).map(r => r.solvent + "|" + r.arch)) !== JSON.stringify(["THF|RDE 1600 rpm", "THF|rotating cyl. 3000 rpm"]))
  throw new Error("S6.2/S6.4: the liquid-cooling verdicts that move on the stack gap, stack current or inherited sigma have changed");
// SI Table S12 (G-THERMAXIS, results/thermal_axis_sweeps.json): every change of cooling class inside a declared input's
// tested range. S6.2 points to it once; every Table S7 row whose input moves a class points to it as well.
const S12_PRETTY = (t) => String(t).replace(/cm-2/g, "cm\u207b\u00b2").replace(/W m-2 K-1/g, "W m\u207b\u00b2 K\u207b\u00b9")
  .replace(/(\d)x\b/g, "$1\u00d7").replace(/\bum\b/g, "\u00b5m").replace(/(\d) C\b/g, "$1 \u00b0C").replace(/\bsigma\b/g, "\u03c3")
  .replace(/kappa\(T_b\)/g, "\u03ba(T_b)").replace(/\bi0\b/g, "i\u2080").replace(/\balpha\b/g, "\u03b1").replace(/V\^2\/3/g, "V^(2/3)");
const S12_ROWS = TAX.table.map(t => [t.cell, t.solvent === "aq. NaOH" ? "aq. NaOH" : t.solvent,
  S12_PRETTY(t.input + ", " + t.range + " (declared " + t.declared + ")"), t.declared_class, S12_PRETTY(t.classes)]);
const S12_QUIET = TAX.axes.filter(a => a.cells.every(c => !c.changes.length)).map(a => S12_PRETTY(a.label + ", " + a.fmt.replace("%.3g", "%s").replace(/%\.\d[fg]|%s/, String(a.x0)) + " to " + a.fmt.replace("%.3g", "%s").replace(/%\.\d[fg]|%s/, String(a.x1))));
if (!S12_ROWS.length || S12_QUIET.length + TAX.axes.filter(a => a.cells.some(c => c.changes.length)).length !== TAX.axes.length) throw new Error("Table S12: quiet-input count does not close");
const S12_EL = () => [
  mkTable(["Cell", "Electrolyte", "Input, tested range and declared value", "Class at the declared value", "Class across the range"], S12_ROWS, [1250, 850, 2700, 1500, 3400]),
  cap("Table S12. Every change of cooling class inside a declared input's tested range, from the lumped energy balance of §S6.1 at each cell's own operating current. Classes as in §S6.2: passive; liquid cooling, which some cooler within the declared construction range of the cell's own cooler supplies; and beyond liquid cooling, which no cooler in that range supplies. Each input is varied alone about the declared operating point over the tested range given in the third column: the \u03c3 that the recirculating and rotating cells take from the beaker, and the beaker gap, over the factor of 2.5 used for breaking points (the beaker gap from 1 cm, below which the model cools a cell through a plate rather than a jacket), the conductivity across its uncertainty band and up to its value at the boiling point (§S6.3), and each rotation rate through the median current it gives. " + numWordCap(S12_ROWS.length) + " cell\u2013input pairs change class, and every verdict they list is conditional on that input. " + numWordCap(S12_QUIET.length) + " inputs change no class over their ranges: " + listAnd(S12_QUIET) + ".")];
const CF_CYL_THF = CF_V("THF", "rotating cyl. 3000 rpm");
const S12_N_AX = TAX.axes.length, S12_N_MOVE = TAX.axes.filter(a => a.cells.some(c => c.changes.length)).length;
const CF_AXES_SENT = () => " Only THF's duty at the rotating cylinder lies close to the top of its cooler's declared range, " + (100 * (1 - CF_CYL_THF.U_req / CF_CYL_THF.U_liquid[1])).toFixed(0) + "% below it. Table S12 sweeps " + numWord(S12_N_AX) + " declared inputs one at a time over their tested ranges; " + numWord(S12_N_MOVE) + " of them change a cooling class, and the table lists every such change, passive verdicts included, each conditional on the input concerned.";
const CF_LIQ_SENT = () => "Liquid cooling is built as each cell would be cooled, with the cell's own electrolyte-side film, the wall it is cooled through and a laminar water channel heated from one wall (Nu = 5.39) in series: a water jacket over the glass wall of a vessel cell gives U′ = " + CF_LIQTXT("RDE 1600 rpm") + " W cm⁻² K⁻¹ with forced electrolyte flow, and a cooled graphite plate behind the electrode of the stack or chip gives " + CF_LIQTXT("zero-gap PEM stack") + " (Table S7i). "
  + "Against those ranges every duty that needs liquid cooling can be met within its cell's declared construction range: THF's at the " + listAnd(CF_LIQ_ALL.filter(v => v.solvent === "THF").map(v => ARCH_SHORT(v.architecture) + " (" + v.U_req.toFixed(3) + ")")) + " W cm⁻² K⁻¹, and those of " + listAnd([...new Set(CF_LIQ_ALL.filter(v => v.solvent !== "THF").map(v => v.solvent === "aq. NaOH" ? "the aqueous reference" : v.solvent))]) + " at " + Math.min(...CF_LIQ_ALL.filter(v => v.solvent !== "THF").map(v => v.U_req)).toFixed(3) + "–" + Math.max(...CF_LIQ_ALL.filter(v => v.solvent !== "THF").map(v => v.U_req)).toFixed(3) + "." + (CF_LIQ_ALL.every(v => v.U_req <= v.U_liquid[1]) ? "" : (() => { throw new Error("S6.2: a liquid-class duty exceeds its cooler's declared range"); })());
const CF_INBAND = (v, m) => m !== null && m >= v.band_multiple[0] && m <= v.band_multiple[1];
const CF_COND_ACTIVE = CF_ORG.filter(v => v.class !== "passive" && v.conditional);
const CF_FLIPTXT = (v) => { const parts = [];
  if (CF_INBAND(v, v.flip_up_multiple)) parts.push("relaxes to " + (v.class_up === "passive" ? "passive rejection" : v.class_up) + " above " + xmul(v.flip_up_multiple, 2));
  if (CF_INBAND(v, v.flip_down_multiple)) parts.push((v.class_down === "beyond liquid cooling" ? "needs more than its liquid cooling can supply" : "needs " + CF_CLASS_TXT(v.class_down)) + " below " + xmul(v.flip_down_multiple, 2));
  return "the " + ARCH_SHORT(v.architecture) + " in " + v.solvent + " " + parts.join(" and "); };
const CF_BEYOND = CF_ORG.filter(v => CF_INBAND(v, v.flip_down_multiple) && v.class_down === "beyond liquid cooling");
if (CF_THF_CM.some(v => v.class !== "passive" || !v.conditional || v.flip_down_multiple * parseFloat(ELEC.get("3.0 M LiBr/THF").kappa) <= 0.206)) throw new Error("the THF centimetre-gap verdicts no longer turn inside the band above its floor");
// ---- the Onsager limiting law for Bu4NBF4/MeCN: zero at sqrt(c) = Lambda0/(B1 Lambda0 + B2), solvent constants from
// results/kappa_derivation.json (data/derive_kappa.py), whose MeCN viscosity must be the registry's
const KDV = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "kappa_derivation.json"), "utf8").replace(/\bNaN\b/g, "null"));   // Python writes NaN for the non-1:1 rows
// chemistry audit pass 7: the share of the Kohlrausch ceiling each checked row reaches, read from the artifact (it was typed
// "34-72%", the top from a retired NaOH value)
const KD_FRAC = (() => { const f = KDV.rows.map(r => r.frac_of_ceiling).filter(x => typeof x === "number");
  if (f.length !== KDV.rows.length || f.some(x => x >= 1)) throw new Error("kappa_derivation.json: a row lacks its ceiling fraction or exceeds it");
  return Math.round(100 * Math.min(...f)) + "–" + Math.round(100 * Math.max(...f)) + "%"; })();
const KD_MECN = KDV.rows.find(r => r.solvent === "MeCN");
if (!KD_MECN || Math.abs(KD_MECN.eta_mPas - parseFloat(SOLV.get("MeCN").mu)) > 1e-9) throw new Error("kappa_derivation.json is not evaluated at the registry MeCN viscosity; re-run data/derive_kappa.py");
const ONS_C0 = Math.pow(171.1 / (KD_MECN.B1 * 171.1 + KD_MECN.B2), 2);
// Casteel-Amis on the fit Dorn prints (Table 3, p. 1499) at the working molality, against the measured isotherm value
const CA_KAPPA = 33.40 * Math.pow(0.347 / 1.48127, 0.78646) * Math.exp(0.02156 * Math.pow(0.347 - 1.48127, 2) - 0.78646 * (0.347 / 1.48127 - 1));
const CA_MEAS = parseFloat(ELEC.get("0.25 M Bu4NBF4/MeCN").kappa);
const CA_PCT = (100 * Math.abs(CA_KAPPA / CA_MEAS - 1)).toFixed(1);
const comma = (x) => String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
if (!SX.cal_window || !SX.cal_re || SX.n_inside === undefined) throw new Error("schmidt_extrapolation.json lacks the calibration window; re-run data/schmidt_extrapolation.py");
// Eisenberg, Tobias & Wilke fit Eq. IX (p. 312) to five systems over Sc 835-11,490 (Fig. 10 legend, p. 314) and Re 1000-100,000
const EIS_WIN = "Sc " + comma(SX.cal_window[0]) + "\u2013" + comma(SX.cal_window[1]) + " and Re " + comma(SX.cal_re[0]) + "\u2013" + comma(SX.cal_re[1]);

// ---- ex-cell illustrative solve (results/excell.json, written by julia/run_excell.jl) ---------
// Every number in the ex-cell passage of S4 is interpolated from the solver's own JSON, inputs
// included, so the passage cannot drift from the solve (it did: the solver carried a C_sat the
// registry had withdrawn, and the passage printed the numbers that value produced).
const EX = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "excell.json"), "utf8"));
// S5.2 residual-scale argument (pass 17): under c_ref = max(c_bulk, 0.01 c_max,bulk) the ex-cell oxidant's reference is the
// 1 % floor of the largest bulk (the chloride, seeded at C_Cl + 1e-3 mol m-3 in run_excell.jl), and the first-cell terms carry
// delta/dx1 on top of the concentration ratio; dx1 is read from run_excell.jl's own make_problem signature
const XC = (() => {
  const src = fs.readFileSync(path.join(__dirname, "julia", "run_excell.jl"), "utf8");
  const m = /function make_problem\(k_M; N = \d+, dx1 = ([0-9.e-]+), d = delta\)/.exec(src);
  if (!m) throw new Error("S5.2: run_excell.jl's make_problem signature no longer carries dx1");
  const dx1 = parseFloat(m[1]), cref = 0.01 * (EX.inputs.C_Cl_M * 1000 + 1e-3), cmax = EX.c_OX_at_limit_M * 1000;
  return { cref, ratio: cmax / cref, dx1_um: String(Number((dx1 * 1e6).toPrecision(6))), terms: (cmax / cref) * (EX.delta_um * 1e-6 / dx1) };
})();
// The ex-cell partition is solved at the HOCl constant and rises with k (run_excell.jl's k-sweep, on a mesh refined at
// both walls and checked against one twice as fine); the passages below quote it rather than calling it k-independent.
if (!EX.k_sweep || EX.k_sweep.length < 4) throw new Error("excell.json carries no k-sweep; re-run julia/run_excell.jl");
const exAt = (k) => { const e = EX.k_sweep.find(x => Math.abs(x.k_M / k - 1) < 1e-6); if (!e) throw new Error("excell k-sweep lacks k = " + k); return e.infilm_pct; };
if (Math.abs(exAt(EX.k_M) - EX.infilm_pct) > 0.1) throw new Error("the k-sweep does not reproduce the production split at the declared k");
// distance from the film's outer edge at which an instantaneous oxidant would meet the propylene: the propylene flux
// that consumes all of it, i/(2F) per area, is supplied over that distance by diffusion from the bulk
const EX_EDGE_UM = EX.inputs.D_P_m2s * EX.inputs.C_P_mM / (EX.i_op_mAcm2 * 10 / (2 * 96485.332)) * 1e6;
// The ethylene row's in-film regeneration bound: chloride returned by the homogeneous step and weighted by how much of it
// reaches the electrode sums, for a linear film, to the substrate's planar flux n F D C / delta, whatever k is.
const ETH = "Cl-mediated ethylene epoxidation";
const ETH_D = (() => { const L = fs.readFileSync(path.join(DATA, "mediated_substrates.csv"), "utf8").replace(/\r/g, "").trim().split("\n");
  const h = splitCSV(L[0]); const r = L.slice(1).map(splitCSV).find(x => x[h.indexOf("reaction")] === ETH);
  if (!r) throw new Error("mediated_substrates.csv has no row " + ETH); return Number(r[h.indexOf("D_sub_m2s")]); })();
const ETH_RX = csv.slice(1).map(splitCSV).find(r => r[col("reaction")] === ETH);
const ETH_BOUND = Number(ETH_RX[col("n_substrate")]) * 96485.332 * ETH_D * Number(ETH_RX[col("C_substrate_M")]) * 1000 / (EX.delta_um * 1e-6) * 0.1;
// ---- unstirred-batch film derivation (results/free_convection_delta.json) --------------------
const FC = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "free_convection_delta.json"), "utf8"));
// ---- supporting-ion class defaults and what they cost (results/unsourced_D_sensitivity.json) -----
const UD = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "unsourced_D_sensitivity.json"), "utf8"));
// ---- carrier-charge sweep (results/carrier_charge_sensitivity.json, G-ZSENS) --------------------
const ZS = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "carrier_charge_sensitivity.json"), "utf8"));
// G-HOMOZ: the Ni homocoupling, carried at a finite k, re-solved at z = +1 and +2 at that k
const HZ = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "homocoupling_charge_sensitivity.json"), "utf8"));
const ZS_ROWS = new Set(ZS.rows.map(r => r.reaction));
// G-MEDXFER: three solver diffusivities carried in a medium with no tabulated value, bracketed by re-solving (Table S7d)
const MXF = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "medium_transfer_brackets.json"), "utf8"));
// G-XECZ: the cross-electrophile coupling is medium-confidence and published at its sourced k; G-ZSENS re-solves it at k = 0
const XZ = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "xec_charge_sensitivity.json"), "utf8"));
const xzMoves = (z) => XZ.count_moves[z].map(m => m.arch + " \u2265" + m.threshold + " " + m.from + " \u2192 " + m.to).join(", ");
const XZ_TXT = () => { const zs = ["-1", "1", "2"]; const mv = zs.filter(z => XZ.count_moves[z].length);
  return "; the cross-electrophile coupling, published at its sourced rate constant (Table S11), is re-solved at that constant too, where its ceilings move \u00d7" + Math.min(...zs.map(z => XZ.ratio[z][0])).toFixed(2) + "\u2013\u00d7" + Math.max(...zs.map(z => XZ.ratio[z][1])).toFixed(2) + " across the alternatives" + (mv.length ? " and " + mv.map(z => "at z = " + (z === "-1" ? "\u22121" : "+" + z) + " " + xzMoves(z)).join("; ") : " and no threshold count moves"); };
const CC_MED_ZS = CC_MEDIUM.filter(k => ZS_ROWS.has(k));
if (CC_MEDIUM.filter(k => !ZS_ROWS.has(k)).join("|") !== HZ.reaction)
  throw new Error("medium-confidence charges outside both sweeps: " + CC_MEDIUM.filter(k => !ZS_ROWS.has(k)).join("; "));
const HZ_NM = { natural: "unstirred", stirred: "stirred", flow: "recirculating-flow", anec: "ANEC", micro: "microfluidic", rde: "RDE", rce: "rotating-cylinder" };
const hzMoves = (z) => HZ.count_moves[z].map(m => "the " + HZ_NM[m.arch] + " \u2265" + m.threshold + " count from " + m.from + " to " + m.to).join(", ") || "no threshold count";
// ---- the eleven catalyst rows under a finite k (results/catalyst_ec_sensitivity.json, G-CATK) ----
// The published matrix runs every molecular-catalyst row at k = 0: turned over at the electrode,
// credited with no regeneration inside the film, ceiling = the carrier's own transport bound. That
// is the FLOOR of the EC' current, so every sentence that says what the class can and cannot do is
// a k = 0 statement and must say so. G-CATK re-solves the eleven rows as EC' problems over a
// declared k band; nothing below is typed -- every number is read from its artifact.
const CK = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "catalyst_ec_sensitivity.json"), "utf8"));
// 2026-09-11: the Stokes-Einstein radius exposure (results/catalyst_D_sensitivity.json, G-CATD): with the deciding
// catalyst row at its sourced rate constant the ten-of-eleven count is CONDITIONAL on the assigned radius, and the
// S3 passage states the break radius the gate computes rather than a typed margin.
const CD = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "catalyst_D_sensitivity.json"), "utf8"));
// ---- S3.1 and S9.0: the ferrocene benchmark of Eq. S2 and the anchor of Eq. S24 (results/lebas_increment_sensitivity.json).
// The value in common use for ferrocene in MeCN, 2.4e-5 cm2 s-1, has no page here; the one value located on a page is
// Bard & Faulkner's 1.70e-5 (2nd ed., p. 260, Problem 6.12, in 0.5 M Bu4NBF4, quoting Mirkin, Richards & Bard 1993). Both are
// stated, and the radius argument is carried across the two.
const LB = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "lebas_increment_sensitivity.json"), "utf8"));
const FC_HI = LB.ferrocene_measured_cm2s, FC_LO = LB.ferrocene_secondary_cm2s, FC_SC = FC_HI / FC_LO;
if (!(FC_SC > 1)) throw new Error("ferrocene: the page-located value is expected below the value in common use");
const sciFc = (x) => { const e = Math.floor(Math.log10(x)); return (x / Math.pow(10, e)).toFixed(2).replace(/0$/, "") + " × 10" + String(e).replace("-", "⁻").replace(/\d/g, d => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]); };
const cdShort = (nm) => nm.replace(/ \(.*$/, "");
const cdSentence = () => CD.conditional
  ? ("At the assigned radii " + CAT_FRAC() + " catalyst-carried entries clear 25 mA cm⁻² in no architecture, but the count is conditional on this "
     + "input at the sourced rate constants of §S5.7: it breaks at r_h = " + CD.r_crit_from_4p5A.toFixed(2) + " Å on the deciding row (" + cdShort(CD.deciding_row)
     + ", " + CD.second_best_i_lim.toFixed(1) + " mA cm⁻² at best, " + CD.f_crit.toFixed(2) + "× short of the threshold), " + (CD.in_band ? "inside" : "below") + " the assigned " + CD.band_A[0].toFixed(0) + "–" + CD.band_A[1].toFixed(0) + " Å band and above "
     + "the " + CD.r_expected_deciding_A.toFixed(2) + " Å that size-scaling the ferrocene anchor predicts for that complex. The 1/r_h scaling behind that figure is "
     + "the k = 0 law and a bound for the sourced rows, whose ceiling goes as √D in the kinetic regime, which moves the break to " + CD.r_crit_sqrt_from_4p5A.toFixed(2) + " Å"
     + (CD.conditional_under_sqrt_law ? "." : ", below that prediction."))
  : ("The conclusion that rests on it — that " + CAT_FRAC() + " catalyst-carried entries clear 25 mA cm⁻² in no architecture — breaks only at r_h = "
     + CD.r_crit_from_4p5A.toFixed(2) + " Å, below the " + CD.r_expected_deciding_A.toFixed(2) + "–" + (CD.r_expected_deciding_A * FC_SC).toFixed(2) + " Å that size-scaling the two ferrocene values predicts for the deciding row.");
const ckK = CK.k_band_M.map(Number); const ckKmax = Math.max(...ckK);
const ckAt = (k) => CK.per_k[String(k)];
// S5.7, nickel rows: the declared band's k = 1 member lies below every constant measured for a para-substituted aryl bromide
const niK1Sent = () => { const a = ckAt(1); if (!a) throw new Error("catalyst sweep has no k = 1 member");
  const n = a.rows_clearing25.length;
  return "; at k = 1 M⁻¹ s⁻¹, below every one of those measured constants, " + (n === 1 ? "one row of the class still clears" : numWord(n) + " rows of the class clear") + " 25 mA cm⁻²"; };
const ckSurv = (k) => CK.ten_of_eleven_survives_at_k[String(k)];
const ckKhold = (() => { let h = null; for (const k of ckK) { if (ckSurv(k)) h = k; else break; } return h; })();
const ckKfail = (() => { for (const k of ckK) if (!ckSurv(k)) return k; return null; })();
const ckN25 = (k) => ckAt(k).clear25;
const ckAmp = ckAt(ckKmax).max_amplification;
// name the cell behind the band's largest amplification (pass 10 of the chemistry audit: it was unnamed, and it is a chain row)
const CK_AMP_ROWS = Object.entries(CK.per_row).filter(([, v]) => Math.abs(v.max_amplification - ckAmp) < 1e-9).map(([r]) => r);
if (CK_AMP_ROWS.length !== 1) throw new Error("the largest catalyst amplification is not one row's: " + CK_AMP_ROWS);
const CK_AMP_TXT = CK_AMP_ROWS[0] === "Co-H alkene isomerization (catalytic)" ? "the cobalt-hydride alkene isomerization, a chain row the class medians leave out" : (() => { throw new Error("the largest catalyst amplification moved to " + CK_AMP_ROWS[0] + "; name it in §S5.4"); })();
const ckRows = Object.entries(CK.per_row);
const ckCapped = ckRows.filter(([, r]) => r.substrate_capped_at_kmax).length;
const ckClearCapped = ckRows.filter(([, r]) => r.k_min_clearing25 && r.k_min_clearing25.at_substrate_cap).length;
const ckSci = (k) => k >= 1000 ? "10" + { 1000: "³", 10000: "⁴", 100000: "⁵" }[k] : String(k);
const ckShort = (nm) => nm.replace(/ \(.*$/, "");
// The substrate each catalyst row's cap is computed for (data/catalyst_substrates.csv, Wilke-Chang on the exemplar's named substrate).
const CSUBT = fs.readFileSync(path.join(DATA, "catalyst_substrates.csv"), "utf8").replace(/\r/g, "").trim().split("\n").map(splitCSV);
const csubc = (n) => { const i = CSUBT[0].indexOf(n); if (i < 0) throw new Error("catalyst_substrates.csv has no column " + n); return i; };
const catSub = (nm) => { const r = CSUBT.slice(1).find(x => x[csubc("reaction")] === nm);
  if (!r) throw new Error("catalyst_substrates.csv has no row " + nm);
  return r[csubc("substrate")] + " (" + (1e9 * Number(r[csubc("D_sub_m2s")])).toFixed(2) + ")"; };
const ckCsRange = (() => { const c = ckRows.map(([, r]) => r.C_S_M).filter(x => x != null); return c.length ? [Math.min(...c), Math.max(...c)] : null; })();
// 2026-09-11: seven of the eleven rows are carried at a SOURCED rate constant (the G-CATK sourced block;
// docs/CATALYST_RATE_CONSTANTS_20260911.md). Every number below is read from that block.
const SR = CK.sourced || null;
// The catalyst count, stated ONE way everywhere: how many of the class clear 25 mA cm-2 in no architecture
// at the values the matrix publishes. Counted over every catalyst row of the table, the chain row included.
const catNone = () => N_CAT - (SR ? SR.rows_clearing25_anywhere : 0);
const CAT_FRAC = () => numWord(catNone()) + " of " + numWord(N_CAT);
const CAT_FRAC_THE = () => numWord(catNone()) + " of the " + numWord(N_CAT);
const CAT_HYPH = () => numWord(catNone()) + "-of-" + numWord(N_CAT);
// The floor rows the S5.7 paragraph names, asserted against the sweep artifact so the list cannot outlive it.
const FLOOR_NAMED = ["Ni-catalyzed aryl amination (ArBr + amine)", "Electrochemical amination of ArX with NH3", "Co-catalyzed allylic C-H amination",
  "Cathodic aryl-halide radical 5-exo cyclization", "Mn-catalyzed alkene diazidation", "Cu-catalyzed benzylic cyanation",
  "Rh-catalyzed electrooxidative C-H alkenylation", "Doubly decarboxylative Csp3-Csp3"];
const floorRowsWord = () => {
  const f = (SR.rows_floor || []).map(n => n.replace(/ \(.*$/, ""));
  const want = FLOOR_NAMED.map(n => n.replace(/ \(.*$/, ""));
  if (f.length !== want.length || !want.every(n => f.some(x => x === n || x.startsWith(n) || n.startsWith(x))))
    throw new Error("S5.7 names " + FLOOR_NAMED.length + " floor rows; the sweep artifact lists " + JSON.stringify(SR.rows_floor));
  return numWord(f.length);
};
const srK = (k) => ({ 1: "1", 10: "10", 100: "10²", 700: "7 × 10²", 1000: "10³", 10000: "10⁴" })[k] || String(k);
const srRow = (nm) => (SR ? SR.per_row[nm] : null);
// ---- Table S11 rows, from data/rate_constant_basis.csv; sensitivities from the two sweeps' own artifacts
const S6LABEL = new Map(Object.entries(S6MAP).map(([lab, rxn]) => [rxn, lab.replace(/ \(.*$/, "")]));
const KB_RELATIONS = ["same carrier and substrate", "same carrier, other substrates", "analogue of the carrier", "bound from the exemplar's own data", "none measured"];
const kbTableRows = () => KBR.map(r => {
  const rxn = r[kbc("reaction")], cls = r[kbc("carrier_class")], k = Number(r[kbc("k_M1s1")]);
  if (!KB_RELATIONS.includes(r[kbc("relation")])) throw new Error("rate_constant_basis.csv: unknown relation for " + rxn);
  let label, sens;
  if (cls === "mediator") {
    label = S6LABEL.get(rxn); if (!label) throw new Error("Table S11: no Table S6 label for " + rxn);
    if (k === 0) {
      // a row with no measured constant is solved at the floor; a tenfold change of zero is zero, so the cell states the floor
      const cells = EC.filter(c => c.rxn === rxn);
      if (cells.length !== ARCH.length) throw new Error("Table S11: " + rxn + " has " + cells.length + " mediated cells");
      if (cells.some(c => Math.abs(c.ec / c.t0 - 1) > 0.02)) throw new Error("Table S11: " + rxn + " is solved at k = 0 but its cells sit off the commuting bound");
      sens = fcur(Math.max(...cells.map(c => c.ec))) + " (k = 0, the floor)";
    } else {
      const b = kcBest(rxn, "base"), lo = kcBest(rxn, "div10"), hi = kcBest(rxn, "mul10");
      sens = fcur(b) + " (" + fcur(Math.min(lo, hi)) + "–" + fcur(Math.max(lo, hi)) + ")";
    }
  } else {
    const q = srRow(rxn); if (!q) throw new Error("Table S11: no sourced catalyst row " + rxn);
    if (Math.abs(q.k_M - k) > 1e-9 * k) throw new Error("Table S11: " + rxn + " is solved at k = " + q.k_M + " but the record says " + k);
    label = ckShort(rxn);
    const mx = (o) => Math.max(...Object.values(o));
    sens = fcur(mx(q.i_mAcm2)) + " (" + fcur(mx(q.i_at_band_lo)) + "–" + fcur(mx(q.i_at_band_hi)) + "; k " + kSI(q.band_M[0]) + "–" + kSI(q.band_M[1]) + ")";
  }
  const val = r[kbc("printed_value")].replace("{K_THIO}", sci1(K_THIO)).replace("{K_GIESE}", sci1(K_GIESE));
  return [label, r[kbc("step_solved")], kSI(k), r[kbc("measured_system")] + " [⟦" + r[kbc("sources")] + "⟧]", val, r[kbc("relation")], sens];
});
const kbRelationSentence = () => {
  const n = (rel) => KBR.filter(r => r[kbc("relation")] === rel).length;
  const parts = [[n(KB_RELATIONS[0]), "measured for the row's own carrier and substrate"], [n(KB_RELATIONS[1]), "for the same carrier with other substrates"],
                 [n(KB_RELATIONS[2]), "for an analogue of the carrier (another ligand, or the parent of a substituted mediator)"],
                 [n(KB_RELATIONS[3]), "bounds read from the exemplar's own electrolysis or kinetics"], [n(KB_RELATIONS[4]), "declared with no measurement of the step"]];
  if (parts.reduce((a, x) => a + x[0], 0) !== KBR.length) throw new Error("Table S11: the relation classes do not partition the rows");
  const zero = KBR.filter(r => Number(r[kbc("k_M1s1")]) === 0);
  if (zero.some(r => r[kbc("relation")] !== KB_RELATIONS[4])) throw new Error("Table S11: a row at k = 0 must be one with no measurement");
  return numWordCap(parts[0][0]) + " " + (parts[0][0] === 1 ? "is" : "are") + " " + parts[0][1] + ", " + parts.slice(1, 4).map(x => numWord(x[0]) + " " + x[1]).join(", ") + ", and " + numWord(parts[4][0]) + " are " + parts[4][1]
    + (zero.length ? ", " + numWord(zero.length) + " of " + (zero.length === 1 ? "which is" : "which are") + " solved at k = 0, the floor, because neither the literature nor the exemplar's own operation bounds it" : "") + ".";
};
const srBy = (pfx) => (SR ? Object.entries(SR.per_row).filter(([, r]) => r.basis.startsWith(pfx)) : []);
const srCountMoves = () => {
  if (!SR) return "";
  const names = { natural: "unstirred", stirred: "stirred", flow: "recirculating-flow", anec: "ANEC", micro: "microfluidic", rde: "RDE", rce: "rotating-cylinder" };
  const mv = [];
  for (const [a, d] of Object.entries(SR.count_delta_at_band_edges))
    for (const [t, x] of Object.entries(d)) if (x[0] !== 0 || x[1] !== 0) mv.push(names[a] + " ≥" + t + " count " + (x[0] > 0 ? "+" : "") + x[0] + " at the low edge and " + (x[1] > 0 ? "+" : "") + x[1] + " at the high edge");
  return mv.length ? "With every sourced row moved to the edges of the declared band at once, the fifty-row counts move by at most " + SR.max_abs_count_delta + " entr" + (SR.max_abs_count_delta === 1 ? "y" : "ies") + " (" + mv.join("; ") + "); no other count moves." : "With every sourced row moved to the edges of the declared band at once, no ≥25 or ≥50 count moves.";
};
const ckClearList = () => ckAt(ckKmax).rows_clearing25.map(nm => {
  const r = CK.per_row[nm]; const h = r.k_min_clearing25;
  return ckShort(nm) + " (from k = " + ckSci(h.k_M) + " M⁻¹ s⁻¹, highest in the " + ((r) => /^(RDE|ANEC)/.test(r) ? r : r.toLowerCase())(h.reactor.replace(/ \d+ rpm| \(25 um gap\)/, "")) + (h.at_substrate_cap ? ", at its substrate cap" : "") + ")"; }).join("; ");
// The Ni-XEC row's recirculating-flow cell across the band: the third reading of the Table S5
// discrepancy, computed from the sweep. Named by reaction and reactor, never by position.
const ckXec = () => {
  const r = srRow("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)");
  if (!r) return "";
  return "At the sourced k = 10² M⁻¹ s⁻¹ (§S5.7) the row's recirculating-flow ceiling is " + r.i_mAcm2.flow.toFixed(1) + " mA cm⁻² (" +
    Math.min(r.i_at_band_lo.flow, r.i_at_band_hi.flow).toFixed(1) + "–" + Math.max(r.i_at_band_lo.flow, r.i_at_band_hi.flow).toFixed(1) +
    " across the declared band; " + r.i_k0_mAcm2.flow.toFixed(1) + " at k = 0), against the 10 mA cm⁻² the campaign ran at — a nominal density on a carbon-felt cathode whose three-dimensional area a planar film does not credit, so the agreement is indicative and is not claimed as a validation.";
};
// The wall census: how many finite-k cells end on a ramp wall, and how tight those walls are.
const ckWalls = () => {
  const w = CK.walls; if (!w) return "";
  return w.wall_cells + " of the " + w.finite_k_cells + " finite-k cells end on a Newton wall of the current ramp. Each is a lower bound, and each is tight: the concentration-control walk that follows reaches a plateau at which the exhausted species — the resting carrier, or the substrate where the reaction front detaches and the current runs above the carrier's own cap — is at no more than " + (100 * w.exhausted_fraction_max_walls).toFixed(2) + " % of its bulk value at the electrode (median " + (100 * w.exhausted_fraction_median_walls).toFixed(2) + " %; " + (100 * w.exhausted_fraction_max_all).toFixed(2) + " % over every finite-k cell), the same test §S5.2 applies to the mediated matrix. No cell reported below either threshold could reach it within its own tightness, so the census is decidable in every cell.";
};
// ONE sentence, used by every passage that states the catalyst result, so they cannot disagree.
const ckSentence = () => {
  if (!SR) return "The catalyst rows are carried at k = 0, the floor of the EC′ current (§S5.7).";
  const ni = srBy("Ni(I)bpy"), co = srBy("Co-H");
  const g = SR;
  if (ni.length + co.length !== g.n_sourced) throw new Error("ckSentence names nickel and cobalt-hydride sourced rows only; the artifact has " + g.n_sourced);
  return numWordCap(g.n_sourced) + " of the " + numWord(N_CAT) + " rows are carried at a rate constant measured (nickel) or estimated by voltammetric simulation (cobalt hydride), on a related system, for the step that consumes the substrate and transferred to the row as a declared choice (§S5.7): the " + numWord(ni.length) +
    " nickel rows at k = 10² M⁻¹ s⁻¹ (oxidative addition of an aryl bromide to a low-valent nickel bipyridine, measured at 3.4–56 on related complexes and bounded at ≳10² in DMF by the amination exemplar\'s own voltammetry, and swept over 10¹–10⁴) and the " + numWord(co.length) +
    " cobalt-hydride rows at 7 × 10² (the Co(III)–H step with a styrene, simulated as an insertion); the other " + numWord(g.n_floor) +
    " carry no measured constant and stay at k = 0, the floor of the EC′ current. At those values " + CAT_FRAC_THE() + " clear 25 mA cm⁻² in no architecture" +
    (g.ten_of_eleven_holds_at_band.every(x => x) ? ", at both edges of every bracket" : "") +
    "; the " + numWord(g.n_sourced) + " sourced rows have reaction layers already thinner than every film, so thinning the film from the unstirred to the rotating-cylinder archetype buys " +
    g.gain_sourced_min.toFixed(1) + "–" + g.gain_sourced_max.toFixed(1) + "× where the same rows gave " + fRange(Object.values(g.per_row).map(r => r.gain_at_k0), v => v.toFixed(0)) +
    "× at k = 0. The class is concentration-capped either way: by the carrier where the homogeneous step is slow, by the dilute substrate where it is fast" +
    (ckCsRange ? " (substrates at " + ckCsRange[0].toFixed(3).replace(/0+$/, "").replace(/\.$/, "") + "–" + ckCsRange[1].toFixed(2) + " M)" : "") + ".";
};
const ckBandSentence = () =>
  "Re-solved over the whole declared band, " +
  (ckKfail === null
    ? "no catalyst row clears 25 mA cm⁻² at any k up to " + ckSci(ckKmax) + " M⁻¹ s⁻¹"
    : "at most one row clears 25 mA cm⁻² for k ≤ " + ckSci(ckKhold) + " M⁻¹ s⁻¹ and more than one does at k = " + ckSci(ckKfail) +
      " M⁻¹ s⁻¹" + (ckKfail === ckKmax ? "" : "; by k = " + ckSci(ckKmax)) + ", " + ckN25(ckKmax) + " of the " + numWord(N_CAT) + " clear 25 mA cm⁻²") +
  "; the largest amplification in the band is " + ckAmp.toFixed(1) + "× and " + ckAt(ckKmax).cells_at_substrate_cap + " of the " + ckAt(ckKmax).cells + " cells sit at their substrate cap at its top.";

// ---- rate-constant sweep (results/rate_constant_sensitivity.json, G-KSENS) ---------------------
const KS = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "rate_constant_sensitivity.json"), "utf8"));
const ksShort = (n) => n.replace(/ \(.*$/, "").replace(" -> ", " → ");
const ksList = () => KS.summary.rows_crossing_25.map(n => {
  const cases = KS.rows.filter(r => r.reaction === n && r.cells_crossing_25 > 0)
    .map(r => (r.factor > 1 ? "×10" : "÷10") + ", " + ["one","two","three","four","five","six","seven"][r.cells_crossing_25 - 1] + (r.cells_crossing_25 === 1 ? " architecture" : " architectures"));
  return ksShort(n) + " (" + cases.join("; ") + ")";
}).join("; ");
if (!ZS.rows.every(r => r.counts_unchanged)) throw new Error("Table S2 caption says no count moves under any alternative carrier charge, but the charge sweep disagrees");
// Sentence-initial counts are spelled out (a caption must not open with a numeral); the count itself is derived.
const NUMW_CAP = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
                  "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty"];
const numWordCap = (n) => (NUMW_CAP[n] ?? String(n));
const numWord = (n) => numWordCap(n).toLowerCase();
const sciD = (v) => { const e = Math.floor(Math.log10(v)); return (v / 10 ** e).toFixed(1) + " × 10" + String(e).replace("-", "⁻").replace(/\d/g, d => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]); };
const udMax = 100 * Math.max(...Object.values(UD.max_rel_change));   // percent
const udEffect = udMax === 0
  ? "leaves every one of the " + N_CELLS + " cells unchanged to the reported precision (the largest relative change is zero) and moves no threshold count in any architecture"
  : "moves no cell by more than " + sciD(udMax) + "% and no threshold count in any architecture";
const fcEnvLo = FC.sensitivity_um["h_5mm"] * FC.sensitivity_um["drho_1e-2"] / FC.delta_centre_um;
const fcEnvHi = FC.sensitivity_um["h_80mm"] * FC.sensitivity_um["drho_1e-3"] / FC.delta_centre_um;
// The unstirred counts across that envelope, with the column scaled as 1/delta: exact for the direct and k = 0 rows and a
// bound on the mediated and catalyst rows, none of which falls faster than 1/delta (chemistry audit, pass 4).
const NAT_FILM = (() => { const d = [...new Set(EC.filter(c => c.reactor === "Unstirred batch").map(c => c.delta))];
  if (d.length !== 1) throw new Error("the unstirred film is not a single fixed value"); return d[0]; })();
const natAt = (d) => { const v = MROW.map(r => Number(r[mcol("natural")]) * NAT_FILM / d);
  return { ge25: v.filter(x => x >= 25).length, ge50: v.filter(x => x >= 50).length }; };
const f2 = (x) => Number(x).toFixed(2);

const KT = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "figK_kappaT_sensitivity.json"), "utf8"));
const ktPair = (reactor, solvent) => {
  const d = (KT.brackets[reactor] || {})[solvent];
  if (!d) throw new Error("figK_kappaT_sensitivity.json has no " + reactor + "/" + solvent);
  return d;
};
const KT_FLIPS = KT.verdict_flips || [];
if (KT_FLIPS.length === 0)
  throw new Error("S6.3 prose reports which verdicts the bracket reverses; the model reports none. "
                  + "Rewrite the paragraph rather than the number.");
const KT_FLIP = ktPair(KT_FLIPS[0].reactor, KT_FLIPS[0].solvent);

// ── the seven-archetype thermal table (2026-09-12) ────────────────────────────────────────────
// S6 used to be written around five reactors with four DECLARED design currents. It now runs on
// Figure 5's own seven archetypes plus the zero-gap reference, each judged against the median
// limiting current the published matrix computes for it, so every number below is interpolated
// from the model's artifacts rather than typed.
const THERM = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "figK_thermal.json"), "utf8"));
const TGEO = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "thermal_geometry_sensitivity.json"), "utf8"));
const T_ARCH = THERM.reactors.map(r => r.name);
const T_IDES = THERM.panelB._design_currents;
const T_CEIL = (sol, arch) => THERM.panelB[sol][arch];
const T_MARG = (sol, arch) => T_CEIL(sol, arch) / T_IDES[arch];
const T_U = Object.fromEntries(THERM.reactors.map(r => [r.name, r.U_passive]));
const T_GAP = Object.fromEntries(THERM.reactors.map(r => [r.name, r.gap_m]));
const T_SOLV = ["THF", "MeCN", "DMF", "aq. NaOH"];
const T_PRETTY = {"THF": "THF", "MeCN": "MeCN", "DMF": "DMF", "aq. NaOH": "aqueous NaOH"};
// rotating-cell boil-off failures that turn inside the kappa(T) bracket (S6.3) or the sigma sweep (S6.4), as [arch, solvent]
if (JSON.stringify(KT_FLIPS.map(f => f.reactor + "|" + f.solvent).sort()) !== JSON.stringify(TGEO.conditional_on_sigma.map(c => c.arch + "|" + c.solvent).sort())
    || !TGEO.conditional_on_inherited_gap.every(c => /RDE/.test(c.arch)) || TGEO.conditional_on_inherited_gap.length !== 2)
  throw new Error("S6.3: the kappa(T) cells are no longer exactly the sigma-conditional four with the disc pair gap-conditional");
const COND_ROT = [...new Map([...KT_FLIPS.map(f => [f.reactor, f.solvent]), ...TGEO.conditional_on_sigma.map(c => [c.arch, c.solvent])]
  .filter(p => /RDE|rotating/.test(p[0])).map(p => [p[0] + "|" + p[1], p])).values()];
const ROT_ROBUST = ["THF", "MeCN", "DMF"].filter(x => !KT_FLIPS.some(f => f.solvent === x && /RDE|rotating/.test(f.reactor)));
if (COND_ROT.some(p => p[1] === "THF") || !ROT_ROBUST.includes("THF")) throw new Error("a THF rotating-cell verdict is conditional; §S6.1 and §S6.3 say none is");
if (T_ARCH.length !== 7)
  throw new Error("S6 is written for the six preparative architectures plus the zero-gap reference; "
                  + "figK_thermal.json carries " + T_ARCH.length + " rows.");
// the architectures that share the beaker gap, read from the table rather than counted by hand
// ---- the S6 quantities the model emits rather than the prose typing them --------------------
// 2026-09-12: five S6 sentences carried numbers the reactor table had moved past (the drop from
// the assumed 0.02 W cm-2 K-1 read "~9%" where the model gives 15-16%, and the wetted-area pairs,
// the h_ext cancellation and the worked example had all been computed on retired inputs).
const TSUP = THERM.si_support;
const _pct = (x) => (100 * x).toFixed(0) + "%";
const _sorder = ["THF", "MeCN", "DMF", "aq. NaOH"];
const _drop = (from, to) => _sorder.map(x => 1 - TSUP.beaker[x][to] / TSUP.beaker[x][from]);
const _rng = (v) => {
  const lo = Math.min.apply(null, v), hi = Math.max.apply(null, v);
  const a = (100 * lo).toFixed(0), b = (100 * hi).toFixed(0);
  return a === b ? a + "%" : a + "\u2013" + b + "%";
};
const ASSUMED_DROP = _rng(_drop("at_assumed_U", "at_geometric_U"));
const WETTED_DROP = _rng(_drop("at_geometric_U", "at_wetted_sigma"));
const WETTED_PAIRS = _sorder.map(x => T_PRETTY[x] + " " + TSUP.beaker[x].at_geometric_U.toFixed(0)
  + " \u2192 " + TSUP.beaker[x].at_wetted_sigma.toFixed(0)).join(", ");
const HEXT_RISE = _pct(TSUP.beaker.DMF.at_hot_h_ext / TSUP.beaker.DMF.at_geometric_U - 1);
const BOTH_PAIR = TSUP.beaker.DMF.at_geometric_U.toFixed(0) + " \u2192 "
  + TSUP.beaker.DMF.at_wetted_sigma_and_hot_h_ext.toFixed(0);
const EX_ECELL = TSUP.worked_example.E_cell_V;
const EX_OHMIC = TSUP.worked_example.ohmic_V;
const EX_Q = TSUP.worked_example.q_Wcm2;
const EX_TSS = TSUP.worked_example.T_ss_C;
// the external film's share of the series resistance, across the architectures the model carries
if (!CF.wall_conduction || CF.wall_conduction.verdicts_changed !== 0) throw new Error("S6.4 says the omitted wall conduction changes no verdict (wall_conduction verdict check)");
const _SHARE = THERM.reactors.map(r => (1 / THERM.h_ext_Wm2K) / (1 / r.h_int + 1 / THERM.h_ext_Wm2K));
const EXT_SHARE = (100 * Math.min.apply(null, _SHARE)).toFixed(1) + "\u2013"
                + (100 * Math.max.apply(null, _SHARE)).toFixed(1) + "%";
const N_THERM_ROWS = census(CAT("Thermal model")).n;
// the kappa(T) bracket, read per reactor and solvent rather than typed
const KT_BEAKER = T_ARCH[0], KT_MICRO = T_ARCH.filter(a => /microfluidic/.test(a))[0];
const ktCeil = (reactor, solvent) => ktPair(
  reactor === KT_MICRO ? "microfluidic 25 um" : reactor, solvent);

const T_SIGMA = (a) => THERM.reactors.find(r => r.name === a).sigma;
// kappa-axis reversal points and the NaI/DMF beaker example, emitted by figs/make_figK.py
// (2026-09-14). The SI typed 12.9x, 20.0x, 2.05x, 1.27x, 187 C and U' = 0.0144 on the retired
// sigma = 12.5 and they outlived the derivation of sigma = 9.96 by a day.
const TFL = TSUP.kappa_flips;
const DMFX = TSUP.beaker_dmf_example;
const KAR = KDV.nai_dmf_ka_route;   // the K_A route for 0.2 M NaI/DMF (data/derive_kappa.py)
if (!(KAR.hi.alpha < KAR.lo.alpha && KAR.hi.kappa_sizecorr_mScm < KAR.lo.kappa_sizecorr_mScm && KAR.mid.kappa_limiting_mScm < 0.5 * KAR.mid.kappa_sizecorr_mScm)) throw new Error("the K_A route no longer splits by conductance form; Table S4's DMF note says it does");
[[DMFX.kappa_E50_20V_mScm, 20], [DMFX.kappa_E50_10V_mScm, 10]].forEach(([k, v]) => { if (!(50 * 10 * DMFX.gap_m / (0.1 * k) / v > 0.5)) throw new Error("the 50 mA cm-2 DMF cell is not ohmic-dominated at kappa = " + k + "; §S6 says most of its voltage is ohmic"); });
const ARCH_SHORT = (a) => a.replace("RDE 1600 rpm", "rotating disc").replace("rotating cyl. 3000 rpm", "rotating cylinder")
  .replace(/microfluidic.*/, "microfluidic chip").replace("zero-gap PEM stack", "zero-gap stack");
const T_PREP = (sol) => Object.entries(TFL[sol]).filter(([a]) => !/zero-gap/.test(a));
const T_BIND = (sol) => T_PREP(sol).filter(([, v]) => !v.passes).sort((x, y) => x[1].multiple - y[1].multiple)[0];
const T_PASSMULT = (sol) => T_PREP(sol).filter(([, v]) => v.passes).map(([, v]) => v.multiple);
const xmul = (x, d = 1) => Number(x).toFixed(d) + "×";
const U_UNST = T_U[T_ARCH[0]], U_STIR = T_U[T_ARCH[1]];
const SIG_B = T_SIGMA(T_ARCH[0]);
// Lobaccaro et al. 2016 Fig. 1 (p. 26778): cell B compartments 2 x 2.2 in, each 0.48 in thick; the two stacked, end plates
// excluded, so this is a LOWER bound on the outer area. Watkins SI Fig. S1c: the parallel H-cell modifies this cell.
const LOB_A = (2 * (2 * 2.2) + 2 * (2 * 0.96) + 2 * (2.2 * 0.96)) * 6.4516;   // cm2 per 1 cm2 cathode
const DMF_TSS_FOLD = DMFX.kappa_Tss_at_boil_mScm / (DMFX.kappa_S_per_m * 10);
const DMF_BIND = T_BIND("DMF"), THF_BIND = T_BIND("THF"), MECN_BIND = T_BIND("MeCN");
const THF_RCE = TFL.THF["rotating cyl. 3000 rpm"].multiple;
const NAOH_NEAR = CF.verdicts.filter(v => v.solvent === "aq. NaOH" && v.flip_down_multiple).sort((a, b) => b.flip_down_multiple - a.flip_down_multiple)[0];
const NAOH_MARG = T_PREP("aq. NaOH").map(([, v]) => v.margin);
const NAOH_RANGE = Math.min.apply(null, NAOH_MARG).toFixed(1) + "–" + Math.max.apply(null, NAOH_MARG).toFixed(1) + "×";
const DMF_BAND_TOP = 16.0;
const DMF_BIND_IN_BAND = DMF_BIND[1].kappa_reverse_mScm < DMF_BAND_TOP;
const THF_PASS_LO = Math.min.apply(null, T_PASSMULT("THF")), THF_PASS_HI = Math.max.apply(null, T_PASSMULT("THF"));
const MCP_DMF_100 = 194;   // J K-1: 100 mL DMF (rho 0.944 g mL-1, c_p 2.06 J g-1 K-1), as stated in S6
const TAU_MIN = (mL) => MCP_DMF_100 * (mL / 100) / (THERM.volume_sweep.U_passive[String(mL)] * 10) / 60;
const T_SHARED = T_ARCH.filter(a => Math.abs(T_GAP[a] - T_GAP[T_ARCH[0]]) < 1e-12);
const T_FAILS = (sol) => T_ARCH.filter(a => T_MARG(sol, a) < 1);
const f1 = (x) => Number(x).toFixed(1);
for (const grp of ["thermal", "transport"]) {
  if (!BOUNDS[grp] || BOUNDS[grp].status) {
    throw new Error("si_sensitivity_bounds.json is incomplete (" + grp + ": " +
      (BOUNDS[grp] ? BOUNDS[grp].status : "missing") + "). Re-run data/si_sensitivity_bounds.py; " +
      "the band-edge mediated solves julia/_bounds_lo.jl and _bounds_hi.jl must both be complete.");
  }
}
const bnum = (x) => (Math.abs(x) >= 100 ? x.toFixed(0) : Math.abs(x) >= 10 ? x.toFixed(1) : x.toFixed(2));
const ARCHLBL = { natural: "unstirred batch", stirred: "stirred batch", flow: "recirculating flow cell",
                  anec: "ANEC flow cell", micro: "microfluidic cell", rde: "RDE 1600 rpm", rce: "rotating cylinder" };

let LEDGER = null;
// what the declared-choice tier (T1) actually holds, read from the ledger (pass 44: the sentence said "the reactor
// archetypes", but every archetype operating point is in the conditional tier)
const LEDGER_T1_TXT = () => {
  const t1 = LEDGER.rows.filter(r => r.tier === "T1");
  const num = t1.filter(r => r.category.startsWith("11.")).length;
  const rest = t1.filter(r => !r.category.startsWith("11.")).map(r => r.parameter).sort();
  if (!(num > 0 && rest.length === 2 && rest[0] === "Illustrative channel pair (S8.1)" && rest[1] === "Temperature T"))
    throw new Error("the ledger's declared-choice tier changed: " + JSON.stringify(rest) + "; describe it in §S9");
  return "the solver discretisation, the isothermal operating point and the illustrative channel pair of §S8.1";
};
try {
  LEDGER = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "assumption_ledger.json"),
                                      "utf8"));
  // The SI reports the PUBLISHED subset, so it must use the ledger's live counts.
  if (LEDGER.n_assumption_live == null) {
    throw new Error("assumption_ledger.json predates the liveness split; re-run "
                    + "data/registry_liveness.py then figs/analysis_assumption_ledger.py");
  }
  if (LEDGER.n_assumption_live !== CENSUS_ALL.assumption) {
    throw new Error("ledger counts " + LEDGER.n_assumption_live + " live assumption rows but the "
                    + "published registry has " + CENSUS_ALL.assumption
                    + "; re-run data/registry_liveness.py then figs/analysis_assumption_ledger.py");
  }
} catch (e) {
  if (!/ENOENT/.test(String(e))) throw e;
  LEDGER = null;
}

// ---------- content ----------
const letter = { size: { width: 12240, height: 15840 } };
const CTR = AlignmentType.CENTER;
const sup = (t) => new TextRun({ text: t, size: 24, superScript: true });
const front = [
  // Title page, matching the manuscript's: same title, same subtitle, same author list and
  // affiliations, same corresponding-author line and date.
  new Paragraph({ alignment: CTR, spacing: { before: 1400, after: 200 },
    children: [new TextRun({ text: "Supporting Information", size: 36, bold: true })] }),
  new Paragraph({ alignment: CTR, spacing: { after: 140 },
    children: [new TextRun({ text: "Reaction engineering for electrified organic synthesis", size: 30, bold: true })] }),
  new Paragraph({ alignment: CTR, spacing: { after: 420 },
    children: [new TextRun({ text: "Perspective for the 10th Anniversary of Reaction Chemistry & Engineering", size: 24 })] }),
  new Paragraph({ alignment: CTR, spacing: { after: 220 }, children: [
    new TextRun({ text: "Justin C. Bui", size: 24 }), sup("1,2,†"),
    new TextRun({ text: ", Alexandria X. Lam", size: 24 }), sup("2"),
    new TextRun({ text: ", Jonas Rein", size: 24 }), sup("1"),
    new TextRun({ text: ", Kasie Leung", size: 24 }), sup("1,3"),
    new TextRun({ text: ", Connor W. Coley", size: 24 }), sup("1"),
    new TextRun({ text: ", Klavs F. Jensen", size: 24 }), sup("1,†") ] }),
  new Paragraph({ alignment: CTR, spacing: { after: 160 }, children: [
    sup("1"), new TextRun({ text: " Department of Chemical Engineering, Massachusetts Institute of Technology, Cambridge, MA 02139, USA; ", size: 20 }),
    sup("2"), new TextRun({ text: " Department of Chemical and Biomolecular Engineering, NYU Tandon School of Engineering, Brooklyn, NY 11201, USA; ", size: 20 }),
    sup("3"), new TextRun({ text: " Department of Chemistry and Chemical Biology, Harvard University, Cambridge, MA 02138, USA", size: 20 }) ] }),
  new Paragraph({ alignment: CTR, spacing: { after: 420 }, children: [
    new TextRun({ text: "† Co-corresponding authors: J. C. Bui (jcbui@mit.edu), K. F. Jensen (kfjensen@mit.edu)", size: 20 })] }),
  // 2026-09-29: the author edited the SI title page in his own copy of the condensed build -- the
  // month, and the removal of the descriptive subtitle, which the MANUSCRIPT's title page does not
  // carry either (its second line is the anniversary note). Ported here because the SI is a build
  // output: left in the .docx alone, the next rebuild would have destroyed both.
  new Paragraph({ alignment: CTR, spacing: { after: 600 },
    children: [new TextRun({ text: "September 2026", size: 24 })] }),
  new Paragraph({ children: [new PageBreak()] }),

  h1("S1. Model overview"),
  h2("S1.1 Modelling assumptions"),
  p("Four modelling choices define the scope of this analysis. Each is stated together with the sensitivity bound used to evaluate its effect; (i) and (ii) are registered in Table S7c, the batch films of (iv) in Table S7g, and (iii) is a statement of scope."),
  p("(i) The transport problem is solved on dilute-solution theory: Nernst\u2013Planck fluxes with a "
     + "constant diffusivity per species, local electroneutrality, unit activity coefficients, and no "
     + "Stefan\u2013Maxwell cross-coefficients (Newman, Ch. 11). This treatment is necessary because the Onsager/Stefan\u2013Maxwell coefficients required by concentrated-solution theory are unavailable for these fifty organic electrolyte compositions. Its consequences can be estimated from measured concentration-dependent conductivity. Dilute theory with concentration-independent mobilities predicts \u03ba \u221d c, i.e. a "
     + "constant equivalent conductance, and the 21-point isotherms of Dorn et al. show the molal conductivity \u03ba/m falling to "
     + "0.44 of its dilute value by 0.80 mol kg\u207b\u00b9 and to 0.05 by 4.50 mol kg\u207b\u00b9 for "
     + "Bu\u2084NBF\u2084/MeCN, and to 0.74 by 1.57 mol kg\u207b\u00b9 for aqueous NaCl. The dilute approximation therefore becomes quantitatively inaccurate above roughly 1 M."),
  p("The influence of concentrated rows can be isolated by splitting the fifty reactions at 1 M "
     + "total dissolved concentration (c = carrier + substrate + supporting electrolyte). This "
     + "division gives "
     + DS.strata.concentrated.n + " concentrated rows and "
     + DS.strata.dilute.n + " dilute rows, and concentration affects the two groups differently. Because i_lim \u221d C, "
     + "concentration raises the ceiling and degrades the theory at the same time, and the two are "
     + "correlated across the set. Of the " + DS.strata.all.n25[0] + " reactions that clear "
     + "25 mA cm\u207b\u00b2 in the unstirred beaker, " + DS.strata.concentrated.n25[0] + " are "
     + "concentrated rows, though those are only "
     + Math.round(100 * DS.strata.concentrated.n / DS.strata.all.n) + "% of the set; within the "
     + "dilute stratum alone the count is " + DS.strata.dilute.n25[0] + " of "
     + DS.strata.dilute.n + ". The dependence weakens as the reactor improves; at the RCE "
     + "the same share is " + DS.strata.concentrated.n25[DS.architectures.indexOf("rce")] + " of " + DS.strata.all.n25[DS.architectures.indexOf("rce")] + " "
     + "because there the ceiling is set by the hydrodynamics rather than by how much "
     + "material is dissolved. Two comparisons bound this sensitivity. The ordering " + ORDERING_TEXT
     + ", holds inside the dilute stratum on its own and inside the "
     + "concentrated stratum on its own, so no conclusion this Perspective draws depends on which "
     + "stratum a reaction falls in; and the departure measured above is an "
     + "**electrolyte** effect, whereas the most concentrated entry in the set, " + DS.c_tot_max_reaction.replace(/ \(.*$/, "").toLowerCase() + " at " + DS.c_tot_max_M.toFixed(2) + " M in all, is mostly neutral substrate, with " + DS.c_tot_max_elyte_M.toFixed(2) + " M salt. On "
     + "supporting-electrolyte molarity the split is "
     + DS.by_electrolyte_molarity["elyte >= 1 M"].n + " rows at \u2265 1 M against "
     + DS.by_electrolyte_molarity["elyte <  1 M"].n + " below it, and the ordering holds in both. "
     + "Threshold counts for the concentrated stratum therefore carry the greatest uncertainty."),
  p("(ii) The viscosity is the pure solvent's, not the solution's. \u03bc in Table S3 is the "
     + "page-anchored CRC value for the neat solvent, used both in Wilke\u2013Chang (D \u221d 1/\u03bc) "
     + "and in \u03bd = \u03bc/\u03c1 for the mass-transfer correlations, while the cells contain solute "
     + "at up to " + DS.c_tot_max_M.toFixed(2) + " M total. A solution is more viscous than the solvent it is made from, so every "
     + "affected ceiling is overstated. Because solution-viscosity measurements are unavailable for these fifty compositions, we instead sweep the ratio (Table S7c). "
     + SV_SENT),
  p("(iii) The model computes a ceiling, not an operating point. There is no electrode kinetics in the "
     + "transport solve: no Butler\u2013Volmer term and no exchange current density (i\u2080 enters only "
     + "the thermal balance of \u00a7S6). Every current density reported here is the transport-limited "
     + "maximum, which a real cell approaches from below and never exceeds. Electrode kinetics are omitted because their rate constants are unavailable for most of the fifty electrode reactions."),
  p("(iv) The diffusion layer is a lumped parameter, not a solved boundary layer. \u03b4 is a measured film for the two flow "
     + "archetypes, the half-gap of the microfluidic channel, and a mass-transfer correlation for the two rotating "
     + "ones; for the two batch archetypes it is a "
     + "measured proxy (stirred, 200 \u00b1 7 \u03bcm) and the free-convection correlation evaluated at a "
     + "declared electrode height and density driving force (unstirred, " + FC.delta_centre_um.toFixed(0)
     + " \u03bcm, carried as 228 \u03bcm) (Table S1); the momentum equations are not solved. Because i_lim scales as 1/\u03b4, uncertainty in \u03b4 has the largest influence on the transport ceiling; Table S7g quantifies this effect for each batch-film estimate."),
  p("The numerical implementation is verified against analytic limits of the adopted theory: Newman's twofold migration enhancement for a binary electrolyte is reproduced to 0.5% and 0.26% (\u00a7S5.6), and discrete charge conservation holds to 3 \u00d7 10\u207b\u00b9\u00b2. Sensitivity analyses further show that none of the reported sweeps reverses the architecture ordering or the order-of-magnitude contrasts on which the conclusions depend. Individual threshold counts are less robust than this ordering, and \u00a7S10 reports their bounds."),
  p("We quantify the transport-limited current density accessible to organic electrosynthesis as a function of reactor architecture, for a set of 50 reactions chosen to represent the published literature. The analysis proceeds in stages. Stage 0 evaluates the Nernst diffusion-layer limiting current for every reaction in seven reactor archetypes: five whose film is a measured or derived constant and two described by established engineering correlations. Stage 1 resolves the diffusion film with a one-dimensional Nernst–Planck model under the electroneutrality constraint, which adds ionic migration, the film potential drop, and the supporting-electrolyte dependence that the Stage 0 picture omits. A companion module evaluates the ohmic cell-voltage stack and the associated Joule-heating ceiling. The transport solvers are implemented in Julia using the finite-volume, log-concentration, damped-Newton architecture of our CO2-reduction continuum model,«bui2022» with no dependency beyond the Julia standard library; the thermal balance, the free-convection film, the Schmidt-range comparison and the conductivity reconstructions are short Python scripts. All of it is archived with this SI."),
  p("Three conclusions follow. First, reactor architecture moves the transport ceiling by more than an order of magnitude: at the reported literature conditions of Table S2, the median limiting current across the 50 reactions rises from " + med("natural") + " mA cm⁻² in an unstirred batch cell to " + medI("flow") + " mA cm⁻² in a recirculating flow cell and to ≈" + medI("rce") + " mA cm⁻² at a turbulent rotating-cylinder electrode, and the number of reactions clearing an industrially relevant 25 mA cm⁻² rises from " + ge25("natural") + " to " + ge25("rce") + ". Second, the benefit is mechanism-dependent: " + (N_DIR - DIR_NEVER.length) + " of the " + N_DIR + " substrate-carried electrolyses clear 25 mA cm⁻² in at least one architecture (the " + numWord(DIR_NEVER.length) + " exceptions are a flow-kinetics study run at 0.02 M and a radical-cation chain tabulated at the 0.1 F mol⁻¹ it passes), whereas " + CAT_NEVER.length + " of the " + N_CAT + " reactions whose current is carried by a dilute molecular catalyst (" + CAT_NEVER_mM + " mM at the verified loadings) clear it in none — the single exception runs at " + CAT_CLEAR_mM + " mM — and " + MED_NEVER.length + " of the " + N_MED + " mediated rows do not either: the 25 mM ACT mediator tops out at " + ACT_TOP + " mA cm⁻², the oxygen-mediated Giese addition, carried by air-saturated oxygen at " + CARR_mM.get("Cathodic Giese (R-I + alkene)").toFixed(2) + " mM, at " + rowBest("Cathodic Giese (R-I + alkene)").toFixed(1) + ", and the triarylamine-mediated oxazole synthesis, carried at k = 0 by " + CARR_mM.get("Oxazole synthesis from ketones and acetonitrile").toFixed(0) + " mM of its mediator, at " + rowBest("Oxazole synthesis from ketones and acetonitrile").toFixed(1) + ". For those rows the ceiling is set by concentration, not convection. " + ckSentence() + " Third, at the current densities that transport engineering makes available, the ohmic-heat term i²L/κ becomes the binding constraint in low-conductivity media unless the inter-electrode gap is reduced in proportion; thermal management, not solvent choice, sets the practical limit."),

  h1("S2. Stage 0: film model and mass-transfer correlations"),
  // NAMING. This SI numbers the three MODEL LAYERS Stage 0 / Stage 1 / Stage 2. Main-text
  // Section 3 numbers REACTOR CLASSES Tier 1 ... Tier 4. Both schemes previously used the
  // word "tier", so "Tier 1" and "Tier 2" each meant two unrelated things across the two
  // documents. "Stage" was chosen because "Level" collides with the TRL-E readiness levels
  // of Section 8 (11 uses) and "Layer" with the diffusion, boundary and reaction layers
  // (49 uses here). The CSV filenames keep the historical tier0_ spelling; renaming them
  // would touch every solver and gate that reads them, so the note below says so instead.
  p("Two numbering schemes appear in this work and they are unrelated. Here Stage 0, Stage 1 and Stage 2 name the three layers of the transport model \u2014 the film expression of Eq. S1, the Nernst\u2013Planck solver of \u00a7S5 and the EC\u2032 solver of \u00a7S5.4, in order of increasing physical detail. Section 3 of the main text uses Tier 1 through Tier 4 for classes of reactor ordered by diffusion-layer thickness. Tier always refers to a reactor and Stage always to a model layer. "),
  p("The limiting current density for a species that must reach the electrode to sustain the reaction is"),
  eqn([{m:[msub("i","lim"), mr("="), mfr([msub("n","c"), mr("F"), msub("D","c"), msub("C","c")], [mr("δ")])]}], "S1"),
  p("where D_c and C_c are the diffusivity and bulk concentration of the transport-limiting current carrier, n_c the electrons delivered per carrier turnover at the electrode, and δ the Nernst diffusion-layer thickness. We classify every reaction by its carrier: (i) direct electrolyses, in which the substrate itself exchanges electrons; (ii) mediated electrolyses, in which a redox shuttle (an oxoammonium, NHPI, a halide, a quinone, a triarylamine, thiocyanate or dissolved O₂) carries the current at its own concentration and n_c counts electrons per shuttle round trip; and (iii) molecular-catalyst electrolyses (Ni, Co, Mn, Cu, Rh), in which the electrode turns over the catalyst, present at 2.6–30 mM at the verified loadings. Equation S1 applied to the carrier, not the substrate, is the ceiling the matrix publishes for the second and third classes — for the mediated rows with the homogeneous step solved (§S5.4), for the catalyst rows at k = 0, the floor of the EC′ current, except the " + numWord(SR.n_sourced) + " solved at a sourced rate constant like the mediated rows (§S5.7); this generalizes the mechanism–transport coupling demonstrated for three reactions by Oliver et al.«oliver2025»"),
  p("δ is obtained per reactor archetype from the correlations in Table S1, evaluated per species because δ depends on D and on the solvent kinematic viscosity ν. Where a correlation applies only above/below a flow-regime boundary we verified the regime (laminar Re < 2300 in the microfluidic channel; the rotating-cylinder correlation is intrinsically turbulent)."),
  mkTable(
    ["Archetype", "Model", "Geometry / operating point", "Correlation", "Ref."],
    [["Unstirred batch", "natural-convection plateau", "vertical plate, quiescent", "δ = 228 μm (fixed)", "derived; the source's own diffusion-layer form δ = 1.48 x (Sc Gr)^−¼ (Eq. XVII) at a declared 20 mm height and Δρ/ρ = 3.2 × 10⁻³ (Wilke, Eisenberg & Tobias, J. Electrochem. Soc. 1953, 100, 513–523). Ref. ⟦bard⟧ defines δ₀ but tabulates no value."],
     ["Stirred batch", "fixed film", "planar electrode in a convecting cell", "δ = 200 μm (fixed)", "measured on a proxy system; 200 ± 7 μm by diffusion-limited current (Williams, Corbin, Zeng, Lazouski, Yang & Manthiram, Sustainable Energy Fuels 2019, 3, 1225–1232, p. 1228). Band 193–207 μm (Table S7g)"],
     ["Recirculating flow cell", "fixed film", "parallel-inlet recirculating H-cell, 280 μL s⁻¹", "δ = 106.9 μm (fixed)", "measured; ferricyanide limiting current on the cell itself (⟦watkins2023⟧, SI Table S1: 106.9 μm experimental, 242 μm by the authors' COMSOL model). Band ±12.1 % (Table S7g)"],
     ["ANEC flow cell", "fixed film", "angled-inlet analytical cell (ANEC), inlet 20° from horizontal toward the electrode, 140 μL s⁻¹", "δ = 36.2 μm (fixed)", "measured; same method and table (⟦watkins2023⟧: 36.2 μm experimental, 57 μm COMSOL; the separate angled-inlet H-cell of the same table, whose bottom inlet faces the electrode at 20°, reads 33.4 μm). Band ±12.1 % (Table S7g)"],
     ["Microfluidic cell", "Lévêque entrance, half-gap floor", "gap 25 μm (0.001 in FEP spacer), τ = 4 min", "δ = h/2 = 12.5 μm for every row", "derived from the printed gap and residence time of ⟦mo2020⟧ (SI p. 13); the Lévêque group is 4h²/(Dτ) exactly, and it lies so far below the fully developed value that the half-gap film binds for all fifty rows (Table S7g)"],
     ["RDE", "Levich", "1600 rpm (declared)", "δ = 1.61 D^⅓ ν^⅙ ω^-½", "measured; coefficient 1.61 as printed by ⟦bard⟧ Sect. 12.4, p. 517 (its reciprocal 0.62 at p. 30, fn. 11), origin ⟦levich⟧"],
     ["Rotating cylinder", "Eisenberg–Tobias–Wilke", "d 1.2 cm, 3000 rpm", "Sh = 0.0791 Re^0.70 Sc^0.356", "correlation measured ⟦eisenberg⟧; fitted over " + EIS_WIN + " (Eq. IX p. 312, Fig. 10 p. 314)"]],
    [1400, 1350, 1800, 1900, 3270]),
  cap("Table S1. Reactor archetypes and mass-transfer correlations, with the provenance state of each entry (registry: Table S7g). δ is evaluated per species from its D and the solvent ν. Three qualifications belong here rather than in a footnote. The two batch archetypes are anchored differently, and the difference matters. The unstirred value rests on two declared inputs: Ref. ⟦bard⟧ contains no numerical δ for natural convection (§1.4.2 defines δ₀ and calls it \"often unknown\"; Eq. 4.4.3 in §4.4.1, p. 147, gives only the √(2Dt) rule of thumb), so δ is derived instead from the diffusion-layer equation Wilke, Eisenberg & Tobias print for exactly this quantity, δ′ = 1.48 x (Sc Gr)^−¼, evaluated over each reaction's own ν and D at a declared electrode height and density driving force: " + FC.delta_centre_um.toFixed(0) + " μm (carried in the model as 228 μm; scaling every unstirred ceiling by the 0.4% difference moves no count), with an envelope of " + fcEnvLo.toFixed(0) + "–" + fcEnvHi.toFixed(0) + " μm over those two declarations. The driving force is the less innocent of the two, because at the limiting current it is set by the concentration the surface depletes and so differs from row to row; one value is declared for all fifty because the densification coefficients of these organic solutions are not available, and Table S7g gives the one case that can be page-anchored (2 M NaCl, for which the film would be " + FC.drho_rho_illustration.delta_um_at_central_height.toFixed(0) + " μm). Across that envelope the unstirred threshold counts run from at least " + natAt(fcEnvHi).ge25 + " to at most " + natAt(fcEnvLo).ge25 + " (≥25 mA cm⁻²) and from at least " + natAt(fcEnvHi).ge50 + " to at most " + natAt(fcEnvLo).ge50 + " (≥50), so the unstirred integers are conditional on these two declarations; no other architecture's count depends on them. An independent measurement of a natural-convection film at a millimetric electrode in quiescent solution, 230 ± 10 μm for 10 mM ferrocyanide in 1 M KCl, brackets that value. The stirred value is a measurement, δ = 200 ± 7 μm, but of a proxy system — dissolved O₂ in a gas-bubbled aqueous cell rather than an organic electrolyte under magnetic stirring — and what that proxy costs is stated in full in Table S7g. Both batch films are therefore central values, and the contrast between them is 1.14×. The two remain close, and the separation is bounded by a declared geometry rather than measured: the unstirred film exceeds the stirred one only for electrode heights above about 12 mm at the central driving force. The three flow films are anchored differently again: the two recirculating cells are measured films, obtained on the cells themselves by the same ferricyanide method as the stirred value but in aqueous electrolyte, and they are applied unscaled to every row, exactly as the stirred film is; the microfluidic film is derived from a printed gap and residence time by the Lévêque entrance solution bounded by the half-gap film, and for that cell the bound is what binds, so the film is the half-gap for every row and the Lévêque coefficient sets no reported number. And the rotating-cylinder correlation was fitted over " + EIS_WIN + " (five systems; Eq. IX, p. 312, and Fig. 10, p. 314), whereas the 50 reactions here span Sc = " + comma(SX.sc_min) + "–" + comma(SX.sc_max) + ", so " + (SX.n_below + SX.n_above) + " of " + SX.n_total + " rows sit outside the calibrated window, " + SX.n_below + " of them below its floor, because aprotic organics raise D and lower ν together. Against the correlation of Jang et al., validated over Sc > 100 and so across this Schmidt range, the per-row rotating-cylinder values fall to " + SX.factor_lo.toFixed(3) + "–" + SX.factor_hi.toFixed(3) + "× and the median from " + SX.medians.rce.toFixed(1) + " to " + SX.medians_alt.rce.toFixed(1) + " mA cm⁻², so the column is bounded below by that comparison rather than by a re-anchoring of its own fit (§S3.3)."),

  h1("S3. Transport-property estimation"),
  h2("S3.1 Diffusivities"),
  p("Direct measurements of diffusion coefficients in the non-aqueous electrolytes used for organic electrosynthesis remain scarce (Section S8). We therefore estimate D for organic carriers with the Wilke–Chang correlation,«wilke1955»"),
  eqn([{m:[mr("D"), mr("="), mr("7.4×"), msup("10","−8"), mfr([msup(mrb([mr("φ"), msub("M","B")]), "1∕2"), mr("T")], [msub("μ","B"), msup(msub("V","A"), "0.6")])]}], "S2", "[cm² s⁻¹]"),
  p("with solvent molar mass M_B (g mol⁻¹), viscosity μ_B (cP), association factor φ (2.6 water, 1.9 methanol, 1.5 ethanol, 1.0 unassociated), and solute molar volume at the normal boiling point V_A (cm³ mol⁻¹) from Le Bas group contributions«poling» computed on the substrate SMILES (atomic increments C 14.8, H 3.7, O 7.4 (12.0 in acids), N 15.6/12.0/10.5 by substitution, S 25.6, halogens F 8.7/Cl 24.6/Br 27.0/I 37.0; ring corrections −11.5 (5-ring) and −15 (6-ring)). Wilke and Chang report an average error of about 10% over 251 solute–solvent systems, and the errors vary so widely that an average means little,«poling» so the one benchmark available here cannot establish a band. For ferrocene in MeCN our implementation gives " + sciFc(LB.ferrocene_D_cm2s) + " cm² s⁻¹ (ring corrections applied, iron at the implementation\u2019s fallback increment, μ = " + LB.ferrocene_mu_MeCN_mPas + " mPa s). The one value we could locate on a page, " + sciFc(FC_LO) + " cm² s⁻¹ in 0.5 M Bu₄NBF₄ (Bard and Faulkner, Electrochemical Methods, 2nd ed., p. 260, quoting Mirkin, Richards and Bard 1993), agrees to " + Math.abs(LB.ferrocene_miss_secondary_pct).toFixed(1) + "%, but it is a secondary citation measured in an electrolyte more viscous than the neat solvent the correlation is given; the " + sciFc(FC_HI) + " cm² s⁻¹ in common use for the neat solvent, which we could not page-anchor, is " + (100 * (FC_HI / LB.ferrocene_D_cm2s - 1)).toFixed(0) + "% above it. We therefore carry ±25% as the working property error below, which is what the sensitivity actually sweeps, rather than the canonical figure. Because i_lim is linear in D, a ±25% property error displaces log₁₀ i_lim by +0.10/−0.12, which is small relative to the order-of-magnitude spreads that separate reactor archetypes, and insufficient to move any conclusion in Table S5 except for entries already within ~25% of the threshold."),
  p("Three carrier types receive dedicated treatment. Small inorganic mediator ions (Br⁻, Cl⁻, SCN⁻), for which Wilke–Chang is invalid, use Nernst–Einstein diffusivities from limiting molar conductivities (D = λ°RT/z²F²): the CRC aqueous values«crc» and, in acetonitrile, those of Kalugin et al. (2019, Table 3) for bromide and Krumgalz (1983, Table 4) for thiocyanate. Molecular catalysts use Stokes–Einstein with assigned hydrodynamic radii (4.0–5.0 Å for M(bpy)/M(salen) cores; §S9.0 anchors that choice on ferrocene). The lignin-valorization entry is carried by carbonate (Nernst–Einstein, λ° = 138.6 S cm² mol⁻¹, z = 2), reflecting the verified ex-cell architecture of that pilot process: the cell electrolyzes 1 M Na₂CO₃ to peroxodicarbonate on BDD and the lignin stream (0.1–3 wt% in 3 M NaOH) reacts downstream in an 80-L thermal reactor, never entering the cell.«ruecker2024»"),
    p("Supporting-electrolyte ions in solvents for which no limiting conductance is tabulated — " + UD.n_slots + " cation or anion slots across the fifty rows, " + UD.n_pairs + " distinct ion–solvent pairs, summarised in Table S7d — carry declared values: " + numWord(SLOT_DEF) + " the class defaults, " + sciD(parseFloat(prows.find(r => r[pcol("parameter")] === "Bu4N+/Q+ (organic)")[pcol("value")])) + " m² s⁻¹ for a cation and " + sciD(parseFloat(prows.find(r => r[pcol("parameter")] === "BF4-/generic A- (organic)")[pcol("value")])) + " for an anion, and " + numWord(SLOT_VAL) + " a declared value of another origin, each with its basis in Table S7d. Because a supporting ion carries no flux under local electroneutrality, this assigned diffusivity shapes the potential profile but does not enter the limiting current. Re-solving the full " + N_CELLS + "-cell Nernst–Planck layer with every such value divided and then multiplied by three " + udEffect + " (Table S7d)."),
h2("S3.2 Solvents and electrolytes"),
  mkTable(["Solvent", "M (g/mol)", "μ (mPa·s, 25 °C)", "ρ (g/mL)", "φ", "Source of μ"], S3_ROWS,
     [1700,1100,1400,1000,700,2600]),
  cap("Table S3. Solvent properties used in Eq. S2 and in ν = μ/ρ for the reactor correlations, for the " + S3_ROWS.length + " solvents and solvent mixtures the fifty rows use (full registry with per-entry provenance and state: Table S7b). Two things about this table must be read literally. First, only the product φM enters Eq. S2 — M and φ are never used separately — so for the mixtures the tabulated M is not a molar mass but one half of a presentational split of a single Perkins–Geankoplis product (ref. ⟦poling⟧, Eq. 11-12.4, p. 618); the mixture entries " + S3_MIX.map(r => r[1]).join(", ") + " g mol⁻¹ should not be read as molecular weights. Second, the pure-solvent viscosities are measured, page-anchored to the CRC 97th edition table of viscosity (pp. 6-243 to 6-247), to Krumgalz (J. Chem. Soc. Faraday Trans. 1 1983, 79, 571–587, Table 3, p. 578) for HFIP and to the IAPWS formulation for water. The densities are from the CRC laboratory-solvents table (pp. 15-13 to 15-20) and, for water, IAPWS; Table S7b states the temperature behind each entry" + (S3_RHO_ASSUMED.length ? ", and the density of " + S3_RHO_ASSUMED.join(" and ") + " is a supplier specification" : "") + ". " + "Two mixtures lie inside the range measured by Ansari and Singh (Res. J. Chem. Sci. 2022, 12(1), 67–69, Table-1, p. 68). " + S3_MIX_DERIVED[0] + ", at 43.8 wt% MeCN, is derived: their 40 and 50 wt% rows interpolate to the values carried. For H₂O/MeCN 2:1 v/v, at 28.0 wt%, the 20 and 30 wt% rows interpolate to ρ = " + S3_21.rhoI + " g mL⁻¹, which the carried " + S3_21.rhoC + " matches to its printed precision, and to η = " + S3_21.muI + " mPa s, against which the carried " + S3_21.muC + " is " + S3_21.pct + "% lower; that viscosity is therefore a declared value, and Table S7b states what it can move. The remaining " + nOf(S3_MIX.length - S3_MIX_DERIVED.length - 1, "mixture is an assumption", "mixtures are assumptions") + ". MeCN/H₂O 9:1 v/v is 87.5 wt%, outside the measured range, and is bracketed by two of its measured points (η between 0.346 and 0.574 mPa s). " + numWordCap(S3_ROWS_SRC.filter(x => /pure-component bracket/.test(x)).length) + " organic blends take a value inside the bracket of their two pure components, each page-anchored in Table S7b. For the aqueous mixtures no isotherm reproducing them at 25 °C and the stated volume ratio could be opened; the CRC concentrative-properties tables are tabulated at 20 °C and indexed by mass per cent, so they cannot support a 25 °C value at a volume ratio and are not cited for one. Because i_lim is linear in D and D ∝ 1/μ, a ±25% error in any of these displaces log₁₀ i_lim by +0.10/−0.12, which is small against the order-of-magnitude spreads separating the archetypes."),

  mkTable(["Electrolyte", "κ (mS/cm)", "State", "Margin before a stated conclusion flips", "Note"],
    [["3.0 M LiBr / THF","3.0","assumption",xmul(THF_BIND[1].multiple) + " (binding verdict, " + ARCH_SHORT(THF_BIND[0]) + "), against a band top of " + xmul(CF_V("THF", "RDE 1600 rpm").band_multiple[1], 2) + "; liquid cooling within the declared construction range stops sufficing below " + CF_THF_LIQ_TXT() + " (§S6.2)","§S6 THF entry. Ref. ⟦peters2019⟧ SM p. S15 page-anchors the 3.0 M composition, not κ; the value came from the row's own note that this is a heavily ion-paired ether medium. THF (ε = 7.6) has a Bjerrum distance of 3.7 nm, so association is essentially complete and κ cannot be derived either. Band 0.2–6.6 mS cm⁻¹, with a state-B hard floor of 0.206 mS cm⁻¹ obtained from the total cell resistance of the flow-Birch cell of Lee et al., Org. Process Res. Dev. 2022, 26, 2674–2684 (R_tot ≤ V/I = 3.2 V / 0.520 A in a coaxial annulus whose geometry follows from the stated 17.8 mL annulus volume). Judged against each architecture's own transport ceiling, the binding verdict is the " + ARCH_SHORT(THF_BIND[0]) + ", which reverses only at " + xmul(THF_BIND[1].multiple) + " the carried conductivity against a band whose top is " + xmul(CF_V("THF", "RDE 1600 rpm").band_multiple[1], 2) + ". The §S6.2 liquid-cooling verdicts are tighter: THF's liquid cooling within the declared construction range stops sufficing below " + CF_THF_LIQ_TXT() + " the carried conductivity, inside the band, and §S6.2 states them conditionally. Across the 0.2–6.6 band the boil-off verdicts of the microfluidic chip, the rotating cells and the stack do not turn: the chip clears at every point and the other three fail at every point. The unstirred, stirred and recirculating cells do move: each clears at the carried value and boils before reaching its own transport ceiling only below " + listAnd(CF_THF_CM.map(v => (v.flip_down_multiple * parseFloat(ELEC.get("3.0 M LiBr/THF").kappa)).toFixed(2))) + " mS cm⁻¹ (" + listAnd(CF_THF_CM.map(v => ARCH_SHORT(v.architecture))) + "), inside the band and above its state-B floor of 0.206 mS cm⁻¹."],
     ["0.25 M Bu4NBF4 / MeCN","19.95","measured",xmul(MECN_BIND[1].multiple, 2) + " (binding verdict, " + ARCH_SHORT(MECN_BIND[0]) + "); " + xmul(TFL.MeCN["rotating cyl. 3000 rpm"].multiple, 2) + " at the rotating cylinder","§S6 MeCN entry. MEASURED: read off the raw κ(c) isotherm in the Supporting Information of Dorn, Kareth, Weidner and Petermann, J. Chem. Eng. Data 2024, 69, 1493–1502. A cross-check — Casteel–Amis (Casteel and Amis, J. Chem. Eng. Data 1972, 17, 55–59) applied to the fit the same article prints in Table 3, p. 1499 (κ_max 33.40 mS cm⁻¹, m̄_max 1.48127 mol kg⁻¹, a 0.78646, b −0.02156), evaluated at m̄ = 0.347, the molality at which the measured value lies on the isotherm (the solution-density conversion, with ρ(MeCN) = 0.7768 g cm⁻³ and a declared apparent molar volume V_φ = 287 cm³ mol⁻¹, gives 0.348) — returns " + CA_KAPPA.toFixed(2) + " mS cm⁻¹, " + CA_PCT + "% from the measured value, with the sign of b that reproduces the κ_calc column Dorn prints beside every measured point; the measurement is the value adopted because it is the datum the fit was made from. Cross-checked at 1 M against Gong, Fang, Gu, Li and Yan, Energy Environ. Sci. 2015, 8, 3515–3530, Table 3, p. 3519, whose 32.3 mS cm⁻¹ the same fit reproduces to within 2%. Band 15–23 mS cm⁻¹. A mass-action bound of 24–36 mS cm⁻¹ is not used: it is a Lee–Wheaton extrapolation some 25× above its own fitted range."],
     ["0.2 M NaI / DMF",NAI.k,"derived",xmul(DMF_BIND[1].multiple, 2) + " (binding verdict, " + ARCH_SHORT(DMF_BIND[0]) + (DMF_BIND_IN_BAND ? ", inside the 4–16 band" : "") + "); " + xmul(DMF_TSS_FOLD, 2) + " for the §S6 steady-state sentence; ×" + (DMFX.kappa_E50_10V_mScm / Number(NAI.k)).toFixed(2) + " and ×" + (DMFX.kappa_E50_20V_mScm / Number(NAI.k)).toFixed(2) + " for the " + DMFX.E_cell_50_V.toFixed(1) + " V statement","§S6 DMF entry, and the most exposed number in the registry. λ°(Na⁺) = 29.81 and λ°(I⁻) = 52.11 S cm² mol⁻¹ in DMF at 25 °C are page-anchored to Gopal and Jha, Indian J. Chem. 1977, 15A, 80–83, Table 2, p. 81, giving Λ°(NaI, DMF) = 81.9 ± 0.8 by Kohlrausch additivity, which corroborates to 0.7% the direct measurement Λ° = 81.35 ± 0.03 (Krumgalz and Barthel, Z. Phys. Chem. 1984, 142, 167–178, Table 2, p. 170) that is the value adopted — and with it a hard ceiling κ ≤ cΛ° = 16.27 mS cm⁻¹. Λ(c) at 0.2 M has never been measured for this salt in this solvent, so the attenuation is transferred instead: Dorn's Supporting Information measures NaI in methanol across the full range, and with Λ°(NaI, MeOH) = 107.86 the measured Λ/Λ° at 0.2 M (molality " + NAI.m + " mol kg⁻¹ for an apparent molar volume of NaI of 0–35 cm³ mol⁻¹) is " + NAI.rr + ", giving κ = 0.2 × 81.35 × " + NAI.r + " = " + NAI.k + " mS cm⁻¹. The single assumption — equal attenuation at equal molarity — is known to err in one direction, since DMF's permittivity (36.8, Kinart Table 1) is the higher of the two, it pairs less, so " + NAI.k + " is expected to err low rather than being a best estimate; calibrating the Onsager limiting law on that same methanol measurement gives a higher estimate. The low-side value is carried because its derivation is the shorter of the two. A third route uses only same-system measurements: Krumgalz and Barthel's association constant, K_A = 7.50 ± 0.57 dm³ mol⁻¹, with Debye–Hückel activity coefficients at their distance parameter of 1.131 nm, gives a free-ion fraction of " + KAR.hi.alpha.toFixed(2) + "–" + KAR.lo.alpha.toFixed(2) + " at 0.2 M. Turning that fraction into κ needs a conductance equation far outside the range they fitted, and the form decides the answer: " + KAR.mid.kappa_limiting_mScm.toFixed(1) + " mS cm⁻¹ by the Onsager limiting law and " + KAR.hi.kappa_sizecorr_mScm.toFixed(1) + "–" + KAR.lo.kappa_sizecorr_mScm.toFixed(1) + " with its ion-size factor, so that route bounds nothing. The permittivity argument fixes a direction, not a bound. The " + ARCH_SHORT(DMF_BIND[0]) + " verdict and the two sentences of §S6 that rest on this row are quoted with their margins."],
     ["1 M NaOH (aq)","174.5","measured",xmul(1 / NAOH_NEAR.flip_down_multiple) + " fall (" + ARCH_SHORT(NAOH_NEAR.architecture) + ")","§S6 aqueous reference. The applicable CRC table is not p. 5-74 (Vanýsek, equivalent conductivity, 25 °C, c ≤ 0.1 M, whose NaOH row stops at 0.01 M). CRC Section 5 also carries \"Electrical Conductivity of Aqueous Solutions\" at p. 5-71 (20 °C, 0.5–50 mass %), which reaches every concentrated aqueous row here. Derived: c ↔ mass % from \"Concentrative Properties of Aqueous Solutions\" (20 °C; 1.000 M NaOH = 3.840 mass %), κ(mass %) from p. 5-71 (NaOH 2% = 93.1, 5% = 206 mS cm⁻¹) → 162–166 mS cm⁻¹ at 20 °C, corrected 20 → 25 °C at α = 1.5–1.9%/K for hydroxides → 174–182. Band 174–182, centred on 178; the adopted measurement of 174.5 sits at its lower edge, which corroborates it. Pipeline validated against ASTM D 1125-95(2005) Table 1 Reference Solution A (1 demal KCl, 7.11352 mass %, 111.342 mS cm⁻¹ at 25 °C) to within +0.3 to +1.2%. Robust regardless: the boil-off ceilings exceed the transport ceilings " + NAOH_RANGE + ", and the nearest conductivity reversal needs a " + xmul(1 / NAOH_NEAR.flip_down_multiple) + " fall."],
     ].map(r => fromCSV(r, [[1,"kappa",null],[2,"state",null]], elecRow, "S4")),
    [2200,750,900,1350,4800]),
  cap("Table S4. Ionic conductivities (25 °C) quoted in the ohmic and thermal analysis of Section S6, with the provenance state and per-row margin of the registry (Table S7f). Of the " + CENSUS_COND.n + " registered conductivities, " + CENSUS_COND.derived + " " + isAre(CENSUS_COND.derived) + " derived and " + nOf(CENSUS_COND.assumption, "an assumption", "assumptions") + " in the sense of §S9; " + (CENSUS_COND.measured ? CENSUS_COND.measured + " " + (CENSUS_COND.measured === 1 ? "reaches" : "reach") + " the measured state" : "none reaches the measured state") + ". Row by row: 0.25 M Bu₄NBF₄/MeCN, 1 M NaOH aq and 0.1 M Bu₄NBF₄/DMF (quoted in §S6 but not tabulated here) are measured, the first two read off raw κ(c) isotherms in the Supporting Information of Dorn et al. 2024 and the third from Shinkle et al., J. Power Sources 2014, 248, 1299–1305, Table 1; 0.2 M NaI/DMF is derived, by transferring a measured attenuation Λ/Λ° onto a directly measured Λ° (Eq. S27 and §S9); and 3.0 M LiBr/THF remains an assumption, the one conductivity here with no source for its value. The three measured rows are measured at their working concentration — two read off raw isotherms, one a tabulated measurement — rather than reconstructed from a limiting-conductivity table, for a reason that is specific and checkable: evaluated with the measured Λ° = 171.1 S cm² mol⁻¹ for Bu₄NBF₄/MeCN, the Onsager limiting law goes negative above " + ONS_C0.toFixed(3) + " M, so no λ° table can supply κ across the 0.03–1 M range these architectures use. The tightest margins that fall inside their own conductivity bands are the THF liquid-cooling verdicts, which leave the declared cooler range below " + CF_THF_LIQ_TXT() + " (Table S12), and the DMF entry, whose binding verdict reverses at " + xmul(DMF_BIND[1].multiple, 2) + ", whose §S6 steady-state sentence flips at " + xmul(DMF_TSS_FOLD, 2) + " and whose " + DMFX.E_cell_50_V.toFixed(1) + " V cell-voltage statement leaves the 10–20 V band at ×" + (DMFX.kappa_E50_10V_mScm / Number(NAI.k)).toFixed(2) + " and ×" + (DMFX.kappa_E50_20V_mScm / Number(NAI.k)).toFixed(2) + ". Two facts bound what that costs. First, κ enters no transport quantity — Eq. S1 and the Nernst–Planck and EC′ solvers use D, C, δ and z only — so a conductivity bears only on the ohmic and thermal statements: the four §S6 electrolytes and 0.1 M Bu₄NBF₄/DMF, which carries the cell-voltage example of Section 9.1 of the main text. Second, the four §S6 entries have individually computed margins, given above and in Table S7f, and every statement resting on one is qualified in §S6.1, §S6.2 and §S6.3 by that margin."),

  h2("S3.3 Extrapolation of the rotating-cylinder correlation"),
  p("Table S1 gives each archetype its correlation and its provenance. One of the four is applied "
     + "outside the range it was established over, and because it sets the column carrying the "
     + "most favourable numbers in this work we quantify the resulting uncertainty and its direction. Eisenberg, Tobias and Wilke fit "
     + "their correlation (Eq. IX, p. 312) to five systems, three solid-dissolution and two electrolytic, spanning Sc = "
     + comma(SX.cal_window[0]) + "\u2013" + comma(SX.cal_window[1]) + " (Fig. 10, p. 314), and represent the data by that straight "
     + "line over Re = " + comma(SX.cal_re[0]) + "\u2013" + comma(SX.cal_re[1]) + ". The fifty rows here run "
     + "Sc = " + comma(SX.sc_min) + "\u2013" + comma(SX.sc_max) + " with a median of "
     + SX.sc_median.toFixed(0) + ", so " + SX.n_below + " of " + SX.n_total + " sit below the "
     + "fitted floor, " + SX.n_inside + " inside the window and " + (SX.n_above === 1 ? "one" : String(SX.n_above)) + " above the ceiling. The extrapolation is therefore "
     + "predominantly to low Schmidt number, not high: aprotic organics are low-Sc relative to "
     + "aqueous ferricyanide because their low viscosity raises D and lowers \u03bd together. The "
     + "Reynolds number at this operating point runs " + SX.re_lo.toFixed(0) + "\u2013"
     + SX.re_hi.toFixed(0) + ", inside the fitted range throughout."),
  p("We bound this extrapolation with a second independently fitted correlation. Jang and co-workers\u2019 gastight rotating-cylinder "
     + "cell\u00abjang2022\u00bb yields "
     + SX.alt_correlation.replace("Jang 2022 Eq. 7: ", "")
     + ", fitted independently to the same geometry and validated over Re = "
     + SX.alt_valid_Re[0].toFixed(0) + "\u2013" + SX.alt_valid_Re[1].toFixed(0)
     + " and Sc > " + SX.alt_valid_Sc_min.toFixed(0) + ". The two correlations divide this "
     + "problem between them and neither covers all of it: Eisenberg spans the Reynolds range "
     + "these reactors occupy and is extrapolated in Schmidt, while the second spans the "
     + "Schmidt range \u2014 all " + SX.alt_rows_in_Sc + " of " + SX.n_total + " rows lie "
     + "inside it \u2014 and is extrapolated in Reynolds, where only " + SX.alt_rows_in_Re
     + " of " + SX.n_total + " lie inside. Eisenberg is retained as the primary correlation "
     + "because the Reynolds exponent is the stronger of the two (0.70 against "
     + SX.fitted_p + "), because it covers this operating point completely, and because it is "
     + "the standard correlation for the geometry; the second is used as the bound."),
  p("The difference between the correlations provides a direct bound on this uncertainty and exceeds the effect obtained by perturbing the fitted exponent. Per row the second correlation gives "
     + SX.factor_lo.toFixed(3) + "\u2013" + SX.factor_hi.toFixed(3) + "\u00d7 the current, "
     + "so the rotating-cylinder median falls from " + SX.medians.rce.toFixed(1) + " to "
     + SX.medians_alt.rce.toFixed(1) + " mA cm\u207b\u00b2 ("
     + (100 * (SX.medians_alt.rce / SX.medians.rce - 1)).toFixed(0) + "%), the count clearing "
     + "25 mA cm\u207b\u00b2 goes " + SX.n25_rce + " \u2192 " + SX.n25_rce_alt + " of "
     + SX.n_total + " and the count clearing 50 goes " + SX.n50_rce + " \u2192 "
     + SX.n50_rce_alt + ", and the rotating-cylinder median falls below the rotating-disc value, "
     + "inverting that one adjacent pair. The unstirred-to-rotating span is "
     + (SX.medians.rce / SX.medians.natural).toFixed(1) + "\u00d7 under the primary "
     + "correlation and " + (SX.medians_alt.rce / SX.medians.natural).toFixed(1)
     + "\u00d7 under the second. **The broader architecture ranking is unchanged.** The four-step ordering \u2014 unstirred < stirred < recirculating flow < ANEC "
     + "\u2014 holds identically under both, and the three thin-film archetypes (microfluidic, RDE, "
     + "rotating cylinder) stay above all four under both. The rotating-cylinder column should therefore be read as carrying about a "
     + "thirty per cent correlation uncertainty, and no conclusion here rests on its exact "
     + "value or on its rank against the rotating disc."),
  h1("S4. Reaction set"),
  h2("S4.1 CAS dataset for main-text Figure 1"),
  p("The dataset plotted in main-text Figure 1 was assembled by a two-stage retrieval from CAS content through SciFinder. The two stages do different work, and neither alone is adequate: a keyword search alone admits documents that merely mention electrochemistry, while the filter alone inherits whatever chemical scope the indexing happens to cover."),
  p("**Stage 1, topic query.** The chemical space is bounded by the topic search"),
  new Paragraph({ spacing: { after: 40 }, indent: { left: 360 }, children: [new TextRun({ text: "(\"organic electrosynthesis\" OR \"electroorganic synthesis\" OR electrosynth* OR \"electrochemical organic synthesis\")", size: 18, font: "Consolas" })] }),
  new Paragraph({ spacing: { after: 40 }, indent: { left: 360 }, children: [new TextRun({ text: "AND (oxidation OR reduction OR coupling OR functionalization)", size: 18, font: "Consolas" })] }),
  new Paragraph({ spacing: { after: 40 }, indent: { left: 360 }, children: [new TextRun({ text: "NOT (CO2 OR nitrate OR NO3 OR \"carbon dioxide\" OR \"nitrogen reduction\" OR fuel cell OR semiconductor OR OLED OR photovoltaic)", size: 18, font: "Consolas" })] }),
  p("The exclusions remove adjacent electrochemistry — CO₂ and nitrate reduction, fuel cells, and semiconductor and optoelectronic device work — that would otherwise dominate the hit list without contributing organic transformations."),
  p("**Stage 2, reaction filter.** Within the Stage-1 results the Reactions view is opened and the CAS-curated “Electrochemical” reaction-notes filter applied, which restricts the set to records CAS has indexed as electrochemical transformations rather than documents that merely mention electrochemistry."),
  p("**Deduplication.** Records are deduplicated by CAS reaction number, the earliest reported year retained, giving the 25,941 distinct transformations the figure reports. A reaction appearing in several publications therefore contributes once, dated to its first report, which is what makes the per-year counts of Fig. 1a a record of first demonstration rather than of publication volume."),
  p("**Atom mapping.** Reactant and product structures are mapped with a transformer-based mapper, with stoichiometry repaired on both sides before mapping is trusted: product-side repair removes duplicate fragments by re-mapping with one fragment withheld and keeping whichever assignment leaves fewest unmapped atoms; reactant-side repair adds a reactant only when more than three heavy atoms are otherwise unaccounted for, choosing the reactant that minimises unmapped atoms on each side. A record is not carried forward if more than 30% of the heavy atoms on either side remain untracked."),
  p("**Classification.** Unreactive spectators and fully untracked fragments are stripped, and records whose product contains a heavy metal are dropped. The remainder are binned by the number of effective reactants and products and classified within each bin: one-to-one records give degenerate entries, isomerization, simple oxidation, simple reduction and functional-group intraconversion; two-to-one records give C–C, C–N, C–O and C–S bond formation and other bond formation; three-or-more-to-one records give multicomponent coupling. Halogenation and cyclization span more than one bin and are decided on their own criteria. Records forming two or more products are left unclassified, fewer than 500 in total. Three descriptors decide every class: the per-element heavy-atom and hydrogen composition difference with the full heavy-atom skeleton, the bond-order-agnostic neighbour multiset at each tracked atom, and the set of product bonds joining two tracked atoms with no counterpart in the reactants."),
  p("**Redox assignment.** The net redox change of the substrate ledger that stacks each bar of Fig. 1b is computed per reaction by summing formal oxidation-state changes over all mapped atoms, seeded at the reacting sites and expanded outward, with explicit corrections where redox is carried by a leaving group. 21,459 records carry the atom-mapped data the assignment requires and are the basis of that panel."),
  p("**Scale and readiness.** The dataset records what was run, not at what scale: no field in it reports mass, volume or throughput. No record is therefore assigned a readiness level individually, and the readiness distribution of main-text Figure 10a is not a classification of these 25,941 transformations. Its lowest tier is the dataset total; the tiers above it are counted independently, from the demonstrations at 20 g or more reported by Lehnherr and Chen«lehnherr2024», the kilogram-scale pharmaceutical programmes reported by Kelly et al.«kelly2026», and the commodity processes of main-text Table 1. The panel bounds how few transformations have been carried above bench scale, and that bound rests on those surveys rather than on the dataset."),
  p("**Operating current density.** The dataset does not report one either, and what its free-text reaction notes do carry cannot stand in for it. A current density \u2014 a current per unit electrode area \u2014 appears in " + DJ.n_stating_j + " of the " + DJ.n_records.toLocaleString("en-US") + " records, " + DJ.share_stating_j_pct.toFixed(1) + "\u00a0% of the set. Those are not " + DJ.n_stating_j + " observations: they carry only " + DJ.n_distinct_notes + " distinct note strings and " + DJ.n_distinct_values + " distinct values, because the index repeats one report\u2019s conditions across every reaction it lists from that report, one string recurring " + DJ.max_note_repeats + " times. The reason a density is so seldom recoverable is that reports give a current: a further " + DJ.n_current_only.toLocaleString("en-US") + " records (" + DJ.share_current_only_pct + "\u00a0% of the set) state one in mA with no electrode area, so no density follows from them. Among the records that do give a density, " + DJ.share_below_25_by_record_pct + "\u00a0% lie below 25\u00a0mA\u00a0cm\u207b\u00b2 (" + DJ.share_below_25_by_value_pct + "\u00a0% of the distinct values), which agrees with the surveyed processes\u00abferretti2025\u00bb, but the subset is too small and too duplicated to characterise the set. The main text therefore reports a threshold rather than an average: the share below 25\u00a0mA\u00a0cm\u207b\u00b2 and the number of records it is drawn from."),
  h2("S4.2 Stratification against the dataset"),
  p("The set is stratified by the reaction-class distribution of our dataset of 25,941 SciFinder-confirmed electrochemical transformations (main text Fig. 1b), of which 21,459 carry the polarity scores Fig. 1b plots. Each exemplar is assigned by applying that classifier's published decision rules to the named transformation, one row at a time (the classification record gives, for each row, the code path in the published classifier that decides it; the resulting class is carried in the cls column of the reaction table, the single source both this document and the figures read). The record applies one convention the published classifier leaves implicit: a reagent that adds only oxygen to the product, water or a peroxide, is not counted as a reactant, while methanol is. It follows how the dataset draws its records — of " + ODONOR.drawn.n_records.toLocaleString("en-US") + ", " + ODONOR.drawn.water + " draw water as a reactant, " + ODONOR.drawn.hydrogen_peroxide + " hydrogen peroxide and " + ODONOR.drawn.methanol + " methanol — and it decides " + numWord(ODONOR.n) + " of the fifty assignments (" + listAnd(Object.entries(ODONOR.by).sort((a, b) => b[1] - a[1]).map(([c, n]) => n + " " + c)) + "). Two of the fifty rows fall outside the comparison basis: the catalytic alkene isomerization, which main-text Fig. 1b does not plot, and one row the classifier leaves unlabelled, exactly as it leaves 925 dataset records unlabelled. Set share against dataset share for the remaining 48: " + stratShares() + ". Every populated class share matches within " + STRAT_BOUND_WORD + " percentage points across the 48 entries the classifier places, and no class is unrepresented — the sparsest, " + stratList(STRAT_SPARSE) + ", carry " + (STRAT_SPARSE_N === 1 ? "one exemplar" : numWord(STRAT_SPARSE_N) + " exemplars") + " each, and multicomponent coupling stands at 6.2% of the set against 6.3% of the dataset, carried by a diazo/thiol/alcohol difunctionalization,«yang2023nc» an alkenesulfonate synthesis from a cinnamic acid, SO₂ and an alcohol«chien2025» and the alkoxysulfonylation entry«mei2019», whose β-methoxy sulfone product incorporates the methanol and so makes it a three-component coupling rather than a two-component C–S formation. On that basis the set is approximately representative of the dataset. The residual gaps are a deliberate over-sampling of " + stratList(STRAT_OVER) + ", the transformations for which verified concentrations and currents are most reliably reported, and a corresponding under-sampling of " + stratList(STRAT_UNDER) + ". It remains a stratified rather than a proportional sample. Neither bears on what the set is used for — every entry is verified individually (Table S2), and the architecture rankings and carrier-class conclusions rest on order-of-magnitude contrasts within each entry rather than on class proportions. One regime is represented by two entries rather than by a class share: chain chemistry, redox-neutral overall, whose charge is set by the experiment rather than by its stoichiometry, for which current density is not the productive constraint and the transport ceiling quantified here is not the operative limit. " + chainSentence() + " The set also deliberately oversamples carrier-borne current — " + (N_MED + N_CAT) + " of 50 entries (" + Math.round(100 * (N_MED + N_CAT) / 50) + "%) are mediated or molecular-catalyst-carried, against a dataset floor of 25% (main text Fig. 1c) — because that is precisely the class for which this analysis shows the transport ceiling to be concentration-capped rather than convection-limited (by the carrier at slow homogeneous kinetics and by the substrate at fast, §S5.7). Within each class we selected named, citable exemplars spanning direct, mediated, and catalyst-carried mechanisms, anchored by the industrial and scaled benchmarks (adiponitrile hydrodimerization;«baizer1964» the BASF 1 mm-gap flow-through methoxylation;«us5507922» the kilogram-scale sulfone oxidation«bottecchia2022» and Ni-catalyzed cross-electrophile coupling«kelly2026»). Where the conditions come from matters, because concentrations set i_lim linearly (Eq. S1). The SciFinder dataset does not supply them: a survey of the aggregated condition notes of 26,790 SciFinder records — a superset containing all 25,941 entries in this dataset — finds molar concentration strings in 0.0% of records and named solvents in 0.6% (currents/controls, by contrast, in 52.9% — reaction databases record what was run, not at what concentration). A structured solvent field is filled for most records, but it names the solvent without its amount, so it fixes no concentration. The dataset therefore fixes only the class stratification of the set. Every concentration, solvent, and electrolyte in Table S2 was instead verified directly against the primary-source PDF of its named exemplar: for each row, the stated amounts and solvent volumes of the paper's standard/scaled conditions (table footnote, figure caption, or experimental section — the anchor is quoted in the final column of Table S2) were converted to molarity by explicit mmol/mL arithmetic. Forty-eight of the fifty rows are verified this way, against the main-article PDF, a patent or the Supporting Material (general-procedure mmol/mL arithmetic; the anchor in Table S2 says which). Two are not, and each is declared rather than counted as verified: the oxygen-mediated Giese addition, whose substrate, electrolyte and cell are the exemplar's but whose carrier is dissolved oxygen, taken at its solubility in air-saturated water at 25 °C (" + CARR_mM.get("Cathodic Giese (R-I + alkene)").toFixed(3) + " mM, Table S7e) as a stand-in for the 2:1 water/acetonitrile medium; and the Cl-mediated ethylene epoxidation, whose electrolyte is quoted verbatim from the exemplar (1.0 M KCl — the paper reads “a flow-cell setup with 1.0 M potassium chloride (KCl) electrolyte, in which ethylene was continuously sparged into the anolyte”) and whose substrate concentration is measured rather than estimated: ethene in 1.000 M KCl is 3.52 mmol L⁻¹, from the IUPAC Solubility Data Series vol. 57 (original measurement Yano, Suetaka, Umehara and Horiuchi, Kagaku Kogaku 1974, 38, 320–323), against 4.83 mmol L⁻¹ in pure water — a 27% salting-out correction that a plain Henry's-law figure omits. The Birch entry runs naphthalene itself under the exemplar's room-temperature general procedure:«peters2019» 0.1 mmol with 0.75 mmol LiBr in 3.5 mL THF (0.029 M substrate, 0.21 M LiBr; SM pp. S12–13), which reduces both rings (1,4,5,8-tetrahydronaphthalene, 75%, SM p. S93), four electrons per naphthalene. The scale campaigns use the TBS ether of p-cresol in a 3.0 M LiBr stock: 0.141 M with 3.5 equiv TPPA in the 10 g batch run (SM pp. S15–16) and 0.18 M with no TPPA in the 100 g flow run (SM pp. S21–22). The BASF methoxylation — whose monograph chapter could not be consulted (the supplied Organic Electrochemistry 4th-ed. scan ends at book p. 834, before Ch. 31, Pütter, pp. 1259–1308«puetter2001») — is instead verified against BASF's own process patents: US 5,507,922«us5507922» (prio. 1993) electrolyzes 15 wt% p-tert-butyltoluene with 0.3 wt% H₂SO₄ in methanol (0.83 M by volume-additive arithmetic, the value the row carries) in an undivided flow-through cell with graphite electrodes 1 mm apart, at 2–10 A dm⁻² (preferably 3–8) and 3–9 F mol⁻¹ (preferably 4–8), inside the 5–50 wt% claim range of the original Degner-era patent (EP 0 011 712, prio. 1978)«ep0011712» and consistent with the 15–20 wt% examples of the meta-isomer successor (US 8,629,304).«us8629304» Three conventions govern that arithmetic, each chosen because the alternative reading is plausible and wrong by a factor of two or more: a catalyst loading quoted in mol% is converted against the substrate concentration rather than read as a molarity (10 mol% at 0.05 M substrate is 5 mM, not 10 mM); a reaction scale stated in mmol is not read as a concentration (the '0.2 mmol scale' entries run at " + MMOL02 + " M); and the solvent tabulated is that of the paper's optimized medium, which is not always the headline solvent (acetone, not MeOH, for waveform-controlled Kolbe; DMA, not DMF, for the kg-scale XEC; nitromethane for the radical-cation Diels–Alder; HFIP for the anodic N–N coupling). Each entry's sensitivity is linear (Eq. S1), so a residual error in any one row rescales that row alone, in proportion — none of the architecture rankings or carrier-class conclusions, which rest on order-of-magnitude contrasts, can be affected by factor-of-two revisions."),
  p("One accounting subtlety deserves an explicit flag. For mediated entries the tabulated i_lim is carried by the mediator, and two regimes must be distinguished. When the homogeneous step occurs inside the diffusion film (in-film EC′, Section S5.4), the substrate must also arrive through the same film and the total-catalysis cap F·n·D_S·C_S/δ bounds the entry. When the mediator is regenerated in the bulk instead — ex-cell mediation — the exemplar is the chloride-mediated alkene epoxidation of Leow et al.:«leow2020» their headline runs oxidize 1.0 M KCl at 300 mA cm⁻² with ethylene sparged into the anolyte, they fix the chloride optimum at 2.0 M on plant-gate cost, and propylene epoxidizes under the same conditions. The system solved here takes that optimum, "
     + EX.inputs.C_Cl_M.toFixed(0) + " M Cl⁻ oxidized at the anode with chlor-alkali physics, and propylene, whose aqueous solubility (C_sat = " + EX.inputs.C_P_mM.toFixed(1) + " mM at 1 atm, Table S7e) makes it the sparingly soluble partner, reacting with HOCl predominantly in the sparged bulk; every input is the registry value (Table S7d, S7e). We verified this partitioning explicitly with the NPP + EC′ solver (mediator generation at the electrode boundary condition, substrate consumption through the homogeneous source term R = k·c_ox·c_S in the film): with k = " + EX.k_M.toFixed(0) + " M⁻¹ s⁻¹ the reaction layer x_k = " + EX.x_k_um.toFixed(0) + " μm is comparable to the film itself (δ = " + EX.delta_um.toFixed(0) + " μm), so the partitioning is settled by the solve rather than by that comparison. At a representative operating point of one third of the carrier limit derived below, " + EX.i_op_mAcm2.toFixed(0) + " mA cm⁻², only " + EX.infilm_pct.toFixed(1) + "% of the generated oxidant (" + EX.i_infilm_mAcm2.toFixed(1) + " mA cm⁻² equivalent — several times the planar-profile propylene diffusion cap, " + EX.i_cap_P_mAcm2.toFixed(2) + " mA cm⁻², the excess reflecting the curved profile inside the reaction zone) reacts within the film; " + EX.exported_pct.toFixed(1) + "% is exported. The split is insensitive to the film: on a " + EX.half_delta_um.toFixed(0) + " μm film at the same current it is " + EX.infilm_pct_half_delta.toFixed(1) + "% in-film and " + EX.exported_pct_half_delta.toFixed(1) + "% exported. It is not insensitive to the rate constant, which here is the HOCl pathway's. A faster oxidant meets the propylene nearer the film's outer edge, so the in-film share rises with k: " + exAt(1e4).toFixed(0) + "% at 10⁴ M⁻¹ s⁻¹, " + exAt(1e5).toFixed(0) + "% at 10⁵ and " + exAt(1e6).toFixed(0) + "% at 10⁶ (solved on a mesh refined at both walls, unchanged to " + (EX.k_sweep_mesh_dev_pct < 0.01 ? "0.01" : EX.k_sweep_mesh_dev_pct.toFixed(2)) + " points on one twice as fine). At the constants measured for Cl₂ with alkenes (Table S6), an oxidant that reacts on contact would be consumed within ≈" + EX_EDGE_UM.toFixed(0) + " μm of that edge, the distance over which diffusion from the bulk supplies the propylene it needs. The export reported above therefore holds for the HOCl pathway, and a Cl₂-dominated anolyte moves the reaction to the outer edge of the film. The solver also resolves two features the analytic bounds miss: a propylene-free, Cl₂-rich zone extending ≈" + (Math.round(EX.propylene_free_zone_um / 10) * 10).toFixed(0) + " μm from the electrode — " + (EX.propylene_free_zone_um / EX.delta_um > 0.6 ? "well over half" : "about half") + " of the film, carrying " + EX.c_OX_at_op_M.toFixed(1) + " M of oxidizing equivalents (" + (EX.c_OX_at_op_M / 2).toFixed(2) + " M as Cl₂ or HOCl, two electrons each) with no alkene to consume it, which is an over-chlorination selectivity risk — and a carrier limit lifted by migration. For this binary electrolyte the analytic limit is twice the Fick bound, since D_salt/(1 − t₋) = 2 D₋ identically: 2 × " + EX.i_fick_Cl_mAcm2.toFixed(0) + " = " + EX.i_analytic_mAcm2.toFixed(0) + " mA cm⁻² at δ = " + EX.delta_um.toFixed(0) + " μm, the factor of 2 for an anion oxidized in its own salt being one of the closed-form limits of §S5.6. The solver reproduces that factor through the EC′ path itself, returning " + EX.reachable_ratio_to_fick.toFixed(3) + " × the Fick bound on a " + EX.reachable_film_um.toFixed(0) + " μm film where the branch can be walked to the collapse criterion"
     + (EX.dcont.every(d => d.converged)
        ? " and, continuing that converged state outward in δ, on " + EX.dcont.map(d => d.delta_um.toFixed(0)).join(", ").replace(/, ([^,]*)$/, " and $1") + " μm films alike (" + EX.dcont.map(d => d.ratio_fick.toFixed(3)).join(", ").replace(/, ([^,]*)$/, " and $1") + " × Fick), so the carrier limit is the solved limit at the production film. Reaching it on the thick films needed one numerical care, stated in §S5.2: the oxidant is a trace in the bulk and molar at the electrode, and each species' conservation residual is scaled by its largest in-film concentration. The state that carries the limit holds " + EX.c_OX_at_limit_M.toFixed(1) + " M of oxidizing equivalents, " + (EX.c_OX_at_limit_M / 2).toFixed(1) + " M as Cl₂ or HOCl (2 D_Cl C_Cl/D_OX in equivalents, independent of δ). A chlorine electrolyte cannot hold molar dissolved chlorine — it leaves the electrode as gas — and this model carries no solubility ceiling and no Cl₃⁻ speciation, the same declared gap as for Br₂ in §S5.5; the carrier limit is a property of the transport equations, reproduced here by the solver and by the closed-form identity, not a statement about the surface composition of a real chlorine anode. "
        : ". Continuing that converged state outward in δ, the branch " + (EX.dcont[0].converged ? "reaches the limit again on a " + EX.dcont[0].delta_um.toFixed(0) + " μm film (" + EX.dcont[0].ratio_fick.toFixed(3) + " × Fick)" : "does not reach the limit even on a " + EX.dcont[0].delta_um.toFixed(0) + " μm film") + " but ends before the carrier is depleted on thicker films — at " + EX.dcont[1].pct_of_analytic.toFixed(0) + "% of the analytic limit on " + EX.dcont[1].delta_um.toFixed(0) + " μm and " + EX.dcont[2].pct_of_analytic.toFixed(0) + "% on " + EX.dcont[2].delta_um.toFixed(0) + " μm. We have not established why. The state that carries the carrier limit holds " + EX.c_OX_at_limit_M.toFixed(1) + " M of oxidizing equivalents, " + (EX.c_OX_at_limit_M / 2).toFixed(1) + " M as Cl₂ or HOCl, on every film (2 D_Cl C_Cl/D_OX in equivalents, independent of δ), outside what a lumped, fully dissolved species can represent — a chlorine electrolyte cannot hold molar dissolved chlorine, which leaves the electrode as gas, and this model carries no solubility ceiling and no Cl₃⁻ speciation, the same declared gap as for Br₂ in §S5.5. The limit is therefore taken from the analytic identity, which requires no such state, and the concentration-controlled solve at " + EX.delta_um.toFixed(0) + " μm is reported as the lower bound it is. ")
     + "The electrode current density is carrier-limited either way (the Fick bound alone is " + EX.i_fick_Cl_mAcm2.toFixed(0) + " mA cm⁻² at this film), and the binding constraint moves to a different unit operation: gas–liquid substrate delivery (k_L·a) must be sized to match the chlorine-generation current, exactly as in the industrial chlorohydrin process. This decoupling of substrate delivery from the inter-electrode gap is the same principle exploited by the Tier-4 architectures of Section 3 (liquid diffusion electrodes; aqueous/non-aqueous soft interfaces)."),
  cap("Table S2 (following pages, landscape). The 50-reaction set with carrier assignments, carrier charge, estimated diffusivities and provenance, concentrations, electron counts, solvent, and electrolyte. z is the charge of the carrier as it reaches the electrode, read from each exemplar paper; it is the switch on the migration term, so a charged carrier in its own salt is lifted above its Fick bound and a neutral one is not. " + numWordCap(CC_MEDIUM.length) + " rows, marked *, carry a medium-confidence charge. " + numWordCap(CC_MED_ZS.length) + " are metal complexes whose electroactive species is written neutral (" + CC_MED_ZS.map(k => k.replace(/ \(.*$/, "")).join("; ") + "); re-solving each at every alternative charge in {" + ZS.alternatives.join(", ") + "} in the k = 0 layer moves its ceilings by at most " + ZS.worst_ceiling_change_pct.toFixed(1) + "% and no threshold count in any architecture" + XZ_TXT() + " (Table S7d). The cathodic Ni homocoupling carries the neutral charge of its precursor, NiBr₂bpy, while its exemplar writes the complex it reduces as Nibpy²⁺; at its adopted rate constant its ceilings rise " + HZ.ratio["1"][0].toFixed(1) + "–" + HZ.ratio["1"][1].toFixed(1) + "-fold at z = +1 and " + HZ.ratio["2"][0].toFixed(1) + "–" + HZ.ratio["2"][1].toFixed(1) + "-fold at z = +2, moving " + hzMoves("2") + ", so those counts are conditional on this charge. The bracketed number opening each C-provenance cell is the exemplar's entry in the reference list; the page/procedure anchor that follows is the location within that source from which the concentrations were computed." + volBasisSentence()),
];

// Reference key(s) for each of the 50 rows, in row order (row 3 cites the Shono protocol and its modern
// Merck exemplar; row 30 cites the three BASF patents). Rendered as a plain [n] prefix on the C-provenance cell.
const ROWKEYS = [
  "kawamata2019", "liu2025", "shono1975", "zhao2021", "fu2017", "malviya2023", "morofuji2013",
  "zhangxu2018", "cai2021", "zhangye2022", "gnaim2022", "hioki2023", "kelly2026", "zhangbaran2022",
  "kirste2012", "mo2020", "liwilden2020", "qiu2018", "cai2022", "courtois1997", "osa1994",
  "baizer1964", "peters2019", "kisukuri2024", "hayashi2022", "yang2023nc", "ke2019", "lopezruiz2018",
  "zhong2021", "us5507922,ep0011712,us8629304", "shono1975", "leow2020", "ruecker2024", "bottecchia2022", "horn2016",
  "chien2025", "cardiel2019", "okada2016", "miller1992", "walecka2022", "gnaim2022", "bao2022",
  "ozaki1994", "zhangzeng2018", "tajima2002", "zhangqiu2025", "mei2019", "gitkis2010", "long2021",
  "gieshoff2016"
];
if (ROWKEYS.length !== rxRows.length) throw new Error("ROWKEYS length " + ROWKEYS.length + " != rows " + rxRows.length);
const rxRowsCited = rxRows.map((row, i) => { const r2 = row.slice(); r2[12] = "[⟦" + ROWKEYS[i] + "⟧] " + r2[12]; return r2; });   // C provenance is column 12 since the z column
const tableS2 = [
  mkTable(["#","Class","Reaction","Carrier","Carrier species","z","D (cm²/s)","C (M)","n_c","Solvent","Electrolyte","D provenance","C provenance"],
    rxRowsCited, [400,900,2400,800,1350,350,900,600,400,900,1500,2100,2340], 14040),
  h2("S4.3 Reactions and electron counts"),
  p("Table S10 writes out the chemistry behind each of the fifty rows: the species that exchanges electrons with the working electrode, the electrode step, the solution step that follows where the carrier is a mediator or a catalyst, and the balanced overall reaction with its electrons. Atoms and charge balance in every row, and the electron count is the one Eq. S1 and Table S2 use. " + numWordCap(N_DIR) + " rows are direct electrolyses, in " + numWord(S10_REAGENT) + " of which the species oxidized is a reagent held in excess, so that the limiting substrate's flux sets the ceiling and is what the row transports; " + numWord(N_MED) + " are carried by a mediator and " + numWord(N_CAT) + " by a molecular catalyst, which the electrode turns over and which reacts with the substrate in solution (§S5.4 and §S5.7). " + numWordCap(S10_PAIRED + S10_CHAIN) + " rows are redox-neutral overall: " + numWord(S10_PAIRED) + " paired cycles, which pass one electron at each electrode per product, and " + numWord(S10_CHAIN) + " chain processes, for which the charge passed per substrate is what the exemplar reports; for those the count is the cycle's own or the charge the exemplar passes, as the table records."),
  cap("Table S10. The reaction behind each row of Table S2. The electrode step is written for the species that exchanges electrons with the working electrode; the overall reaction is balanced in atoms and charge, with e⁻ on the right for an oxidation and on the left for a reduction. e⁻ per substrate is the electron count per molecule of the limiting substrate; a row marked as a paired cycle or a chain has no net electrons in its overall reaction. The last column names the current carrier, whose transport sets the row's ceiling at k = 0; where the homogeneous step exhausts the substrate at the wall, the substrate sets it instead unless migration of a charged carrier still sets the current, and Table S6 gives the limiter for each mediated row."),
  mkTable(["#", "Reaction", "Electrode", "Species exchanging electrons", "Electrode step and what follows", "Overall reaction", "e⁻ per substrate", "Carrier (sets the k = 0 ceiling)"],
    s10Rows, [380, 2100, 760, 1500, 3700, 3900, 850, 850], 14040),
];

// ---- S9.0: the ferrocene anchor of the Stokes-Einstein radius (results/catalyst_D_sensitivity.json) and the anchored
// diffusivities of Eq. S33 (results/anchored_diffusivity.json, figs/anchored_diffusivity.py)
const AD = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "anchored_diffusivity.json"), "utf8"));
const AD_M = [Math.min(...AD.rows.map(r => r.M)), Math.max(...AD.rows.map(r => r.M))];
const AD_R = [Math.min(...AD.rows.map(r => r.ratio)), Math.max(...AD.rows.map(r => r.ratio))];
const FC_MW = 186.04;
const RH_PRED = AD_M.map(m => CD.r_ferrocene_A * Math.pow(m / FC_MW, 1 / 3));
const N_NE = rxRows.filter(r => /Nernst-Einstein/.test(r[11])).length;
// ---------- S9: complete parameter provenance (registry loaded at the top of this file) ----------
const s9 = [
  h1("S9. Parameter provenance"),
  h2("S9.0 Equations for derived parameters"),
  p("Each row of Table S7 carries an Equation column naming the equation that produced it, where one "
    + "equation did. Measured and assumption rows have no entry there, and neither does a derived row "
    + "whose arithmetic is a short chain stated in its own text. "
    + "The equations are collected here so that a reader can go from any tabulated number to the "
    + "arithmetic and the inputs that made it, without reading the source code."),
  eqn([{m:[msub("V","A"), mr("="), mr("Σ "), msub("n","i"), msub("v","i"), mr(" + Σ Δ"), msub("V","ring")]}], "S23", "[cm³ mol⁻¹]"),
  p("Le Bas additive molar volume, the V_A of Eq. S2. Increments v_i and the ring corrections are "
    + "tabulated per element (Table S7c) and cited individually. The assembly is checked: computed "
    + "volumes for ten reference compounds reproduce the published Le Bas values to within 1.7% "
    + "(benzene, toluene, methanol, ethanol, acetone, acetic acid, naphthalene and n-hexane exactly), "
    + "and perturbing any increment fires the check."),
  eqn([{m:[mr("D"), mr("="), mfr([msub("k","B"), mr("T")], [mr("6πμ"), msub("r","h")])]}], "S24", "[cm² s⁻¹]"),
  p("Stokes–Einstein, used for the " + numWord(N_SE) + " metal-complex carriers, for which Eq. S2 is "
    + "unavailable: Le Bas has no transition-metal increment. The hydrodynamic radius r_h = 4–5 Å is "
    + "an assumption and is the most exposed input in the diffusivity column. Inverting this equation "
    + "on ferrocene in MeCN, a neutral metallocene of MW 186, gives r_h = " + CD.r_ferrocene_A.toFixed(2) + " Å at the " + sciFc(FC_HI) + " cm² s⁻¹ in common use and "
    + (CD.r_ferrocene_A * FC_SC).toFixed(2) + " Å at the page-located " + sciFc(FC_LO) + " cm² s⁻¹ of §S3.1, the second an overestimate because that value was measured in a more viscous electrolyte. "
    + "Scaling as M^(1/3) to the " + AD_M[0].toFixed(0) + "–" + AD_M[1].toFixed(0) + " range of these complexes predicts "
    + RH_PRED[0].toFixed(1) + "–" + (RH_PRED[1] * FC_SC).toFixed(1) + " Å across the two, and the adopted 4–5 Å lies in the upper half of that span, so the resulting D is, if anything, "
    + "understated. " + cdSentence()),
  eqn([{m:[mr("D"), mr("="), mfr([msup("λ","0"), mr("RT")], [msup("z","2"), msup("F","2")])]}], "S25", "[cm² s⁻¹]"),
  p("Nernst–Einstein, used for the " + numWord(N_NE) + " small-ion carriers, for which Le Bas volumes are meaningless. "
    + "λ⁰ is taken from a limiting-conductivity table for the ion in its own solvent, except for three ions in mixed or other media, whose values are declared transfers (Table S7d)."),
  eqn([{m:[mr("κ"), mr("="), msub("κ","max"), msup(mrb([mfr([mr("m")],[msub("m","max")])]), "a"),
           mr(" exp"), mrb([mr("−b"), msup(mrb([mr("m − "), msub("m","max")]), "2"),
           mr(" − a"), mrb([mfr([mr("m")],[msub("m","max")]), mr(" − 1")])])]}], "S26", "[mS cm⁻¹]"),
  p("Casteel–Amis. It requires a measured isotherm for that exact salt and solvent: the four fit "
    + "parameters κ_max, m_max, a and b are not predictable. Dorn et al. supply one for Bu₄NBF₄/MeCN, "
    + "on which the Casteel–Amis cross-check of the MeCN row of Table S7f is evaluated; the derived DMF "
    + "conductivity transfers a measured attenuation onto a measured Λ° (Eqs. S27 and S28)."),
  eqn([{m:[mr("κ"), mr("="), mr("Λ"), mrb([mr("c")]), mr(" c")]}], "S27", "[mS cm⁻¹]"),
  eqn([{m:[msup("Λ","0"), mr(" = "), msub("ν","+"), msup(msub("λ","+"), "0"), mr(" + "),
           msub("ν","−"), msup(msub("λ","−"), "0"), mr(",     κ ≤ "), msup("Λ","0"), mr(" c")]}],
      "S28", "[S cm² mol⁻¹]"),
  p("Kohlrausch additivity and the ceiling it implies. The inequality is rigorous for any "
    + "stoichiometry — it assumes complete dissociation AND zero relaxation, and both ion pairing "
    + "and the relaxation effect can only lower κ from there. Each of the " + numWord(KDV.rows.length) + " conductivities "
    + "the registry derives or cross-checks this way was checked against it; all sit under their ceiling, at "
    + KD_FRAC + " of it. The aqueous Λ° used there are read directly from the "
    + "Vanýsek table cited under Eq. S29 (NaOH 247.7, NaCl 126.39, KHCO₃ 117.94 S cm² mol⁻¹). Only "
    + "that table's INFINITE-DILUTION column is used, which is the correct and only quantity a "
    + "ceiling needs; its finite-concentration columns are not applicable to the preparative rows "
    + "here and are not used, exactly as §S6.1 states — its NaOH row stops at 0.01 M and the table "
    + "as a whole stops at 0.1 M. The two statements are consistent: the table bounds these rows "
    + "from above, it does not supply their κ. "
    + "The per-ion values used for the non-aqueous rows are cross-checked against it by Kohlrausch's "
    + "law of independent migration — retrieved electrolyte differences reproduce per-ion differences "
    + "to better than 0.1% (λ⁰(K⁺)−λ⁰(Na⁺) = 23.40 from chlorides and 23.43 from iodides)."),
  eqn([{m:[mr("Λ"), mrb([mr("c")]), mr(" = "), msup("Λ","0"), mr(" − "),
           mrb([msub("B","1"), msup("Λ","0"), mr(" + "), msub("B","2")]), msup(mr("c"), "1∕2")]}], "S29"),
  p("The Debye–Hückel–Onsager limiting law, with B₁ = 8.204 × 10⁵/(εT)^{3/2} and B₂ = 82.5/[η(εT)^{1/2}], "
    + "so that every coefficient follows from the solvent's permittivity and viscosity alone and "
    + "nothing is transferred between salts. Both the equation and its aqueous constants are "
    + "page-anchored to Vanýsek, \u201cEquivalent Conductivity of Electrolytes in Aqueous Solution\u201d "
    + "(CRC Handbook), which prints it as Λ = Λ° − (A + BΛ°)c^{1/2} and gives A = 60.20 and B = 0.229 "
    + "for a symmetric 1:1 electrolyte in water at 25 °C; the formulas above reproduce those to 0.7% "
    + "and 0.3%. Validated on aqueous KCl from the same table: Λ° = 149.79 and Λ(0.01 M) = 141.20 "
    + "S cm² mol⁻¹, against 140.28 computed — a deviation of 0.65%. That table also states its own "
    + "validity limit verbatim, \u201creliable for c < 0.001 mol/L; with higher concentration the error "
    + "increases\u201d, which is 100–3000× below every working concentration in this work. It is reported "
    + "for scale and nothing is inferred from it here, because at every working concentration in "
    + "this work the √c term exceeds 20% of Λ⁰ and the law is outside its validity range — for two "
    + "compositions it returns a negative Λ. This is the quantitative form of the objection stated "
    + "in §S6.1: a limiting-conductivity table cannot supply κ at preparative concentration, and "
    + "only a measured isotherm can."),
  eqn([{m:[msub(mrb([mr("φM")]), "mix"), mr(" = Σ "), msub("x","j"), mrb([msub("φ","j"), msub("M","j")])]}], "S30"),
  eqn([{m:[msub("D","A"), mr(" = "), msub("D","ref"), msup(mrb([mfr([msub("V","ref")], [msub("V","A")])]), "0.6")]}], "S32", "[same solvent, same T]"),
  eqn([{m:[msub("D","A"), mrb([mr("s")]), mr(" = "), msub("D","ref"), mrb([msub("s","ref")]),
           mfr([msub("μ","ref")], [msub("μ","s")]), mfr([msub("r","ref")], [msub("r","A")]),
           mr(",     "), mfr([msub("r","ref")], [msub("r","A")]), mr(" = "),
           msup(mrb([mfr([msub("M","ref")], [msub("M","A")])]), "1∕3")]}], "S33"),
  p("Surrogate-anchored diffusivity: correct a measured D onto a structurally similar species "
    + "instead of predicting one from scratch. Eq. S32 is Eq. S2 written for two solutes in the "
    + "same solvent, so the correlation constant, the association factor, the solvent molar mass, "
    + "T and μ all cancel and only the volume ratio survives; Eq. S33 is the Stokes–Einstein "
    + "analogue, in which μ is the only solvent property that appears and a solvent change is "
    + "therefore also permitted. This matters because the weakness of Eqs. S2 and S24 is their "
    + "PREFACTOR — on ferrocene in MeCN, Eq. S2 lands within 1% of the one page-located value and " + Math.abs(LB.ferrocene_miss_pct).toFixed(0) + "% below the value in common use (§S3.1) — "
    + "and a ratio cancels the prefactor exactly, leaving only the assumption "
    + "that the size-dependence has the right shape between two similar solutes. Where no molar "
    + "volume is available, which is the case for every coordination complex in Table S2 because "
    + "Le Bas carries no transition-metal increment, the radius ratio is taken structurally as "
    + "M^(1/3), i.e. assuming comparable partial molar density between reference and target "
    + "(ferrocene 1.49 g cm⁻³ against 1.4–1.5 for bipyridyl and salen complexes). "
    + "**This construction is not used to overwrite the " + numWord(N_SE) + " catalyst diffusivities.** It gives "
    + "values " + (AD_R[0] / FC_SC).toFixed(2) + "–" + AD_R[1].toFixed(2) + "× the assumed-radius estimate across the two ferrocene values, so the two estimates bracket rather than agree: "
    + "the assumed radius is unsourced, while the anchored value inherits ferrocene's neutrality, "
    + "and the charge and stronger solvation of these complexes raise their effective radius and "
    + "lower their true D. " + (CD.conditional
      ? ("At the sourced rate constants of §S5.7 the " + CAT_HYPH() + " count does depend on the choice: the deciding row sits "
         + CD.f_crit.toFixed(2) + "× short of 25 mA cm⁻² at the assigned radius; at the anchored end of the bracket it would reach " + CD.i_at_anchor_linear.toFixed(1) + " mA cm⁻² if its ceiling scaled as D, the k = 0 law, and "
         + CD.i_at_anchor_sqrt.toFixed(1) + " under the √D scaling of the kinetic regime it sits in, "
         + "so the count is stated as conditional on the radius (Table S7c) rather than as robust to it. ")
      : ("What matters is that the conclusion does not depend on the choice — " + CAT_FRAC() + " catalyst-carried entries clear 25 mA cm⁻² in no architecture at both ends of the bracket. "))
    + "Eq. S33 is also the tool of choice for "
    + "filling a future gap: given a measured D for any structurally similar species in any "
    + "solvent, it transfers that measurement under one stated assumption rather than trusting a "
    + "correlation's absolute prefactor."),

  p("Perkins–Geankoplis mole-fraction rule for the association-factor product of a mixed solvent. "
    + "Only the product φM enters Eq. S2; the split into a nominal M and a nominal φ in Table S3 is "
    + "presentational."),
  eqn([{m:[mr("ν"), mr(" = "), mfr([mr("μ")], [mr("ρ")])]}], "S31", "[m² s⁻¹]"),
  p("Kinematic viscosity, which enters the Schmidt number of every mass-transfer correlation in "
    + "Table S1."),
  p("Table S7 groups every model parameter by category and classifies it as measured, derived, or assumed. Measured values are tied to an external source and a specific locator. Derived values are calculated by a named method from measured or derived inputs. Assumed values are used only when no suitable source is available, and each is accompanied by a sensitivity range and the conclusion it affects. If a conclusion changes within that range, the corresponding statement in this SI is qualified accordingly."),
  p("The three states admit no fourth. In particular no entry is carried as a \"lit-representative\" value — a plausible magnitude for a class of system, tolerant to a factor of about two — because such a value is not distinguishable from an invented number by a reader who cannot check it. The registry is also the only place any constant lives: the " + N_THERM_ROWS + " thermal rows carry the architecture constants rather than leaving them fixed in the code (the external film coefficient, the surface-area ratios σ, the internal film coefficients, the inter-electrode gaps, the boiling points, the cooling-band edges, the emissivity and the ambient temperature). The thermal operating point is not among them: each preparative architecture is judged at its own median transport ceiling from the 50-reaction matrix, so no design current is declared for those six; the zero-gap stack, an industrial reference, runs at its declared 1 A cm⁻² (Table S7i). Locator gives the page, section, table or equation, and is empty only for derived and assumption rows. Sensitivity is mandatory on every assumption row. A citation appears on a row only where it supports the value attached to it at the stated temperature and concentration; where no such source exists the row is a derived or assumption row and says so. Two large parameter families carry per-row provenance in their own tables and are referenced rather than duplicated here: the 50 carrier diffusivities, concentrations and electron counts of Table S2 (each row tagged with its estimation route and exemplar citation), and the " + numWord(N_MED) + " homogeneous rate constants of Table S6."),
  p("Two structural findings bound the exposure that remains, and both were verified independently of the sourcing. First, κ enters only the voltage and thermal path: Eq. S1 and the Nernst–Planck and EC′ solvers use D, C, δ and z alone, so a conductivity bears only on the ohmic and thermal statements of §S6 and on the cell-voltage example of Section 9.1 of the main text. Second, because the external film is " + EXT_SHARE + " of the series thermal resistance, sweeping the internal film coefficient h_int from 50 W m⁻² K⁻¹ to the well-stirred limit moves " + hintSentence() + ". " + loadBearingSentence() + " " + tightestSentence()),
];
const letters = "abcdefghijklmnop";
pcats.forEach((cat, i) => {
  const catRows = prows.filter(r => r[pcol("category")] === cat);
  // Strings that repeat verbatim across three or more rows of a category are factored out into
  // lettered notes below the table. Nothing is lost — the machine-readable registry carries the
  // full string on every row — but it keeps a 268-row appendix legible instead of printing the
  // same 1500-character paragraph forty-five times.
  const noteLabel = new Map(); const noteText = [];
  const NOTE_LETTERS = "αβγδεζηθικλ";
  // Only `sensitivity` is factored: it is the one long column the table actually prints, so a
  // lettered note always has a referring cell. (method_note is not a column here -- see below.)
  [pcol("sensitivity")].forEach(ci => {
    const freq = new Map();
    catRows.forEach(r => { const v = (r[ci] || "").trim(); if (v.length > 120) freq.set(v, (freq.get(v) || 0) + 1); });
    // Ties are broken on the note TEXT, not left to Map insertion order. S_MU and S_RHO stood at
    // 15 occurrences each until 2026-08-30, so which of them was (α) and which (β) was decided by
    // whichever happened to be inserted first -- and giving DMA its own viscosity sensitivity
    // dropped S_MU to 14 and silently swapped both letters throughout a published table. The
    // labels are consistent either way (definition and references come from one map), but a
    // published document should not renumber its own footnotes as a side effect of an unrelated
    // edit. With a text tiebreaker the letters move only when the SET of notes changes.
    [...freq.entries()].filter(([, n]) => n >= 3)
      .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
      .forEach(([v, n]) => {
        if (noteLabel.has(v)) return;
        const L = NOTE_LETTERS[noteText.length] || "*".repeat(noteText.length + 1);
        noteLabel.set(v, L); noteText.push({ L, v, n });
      });
  });
  const fold = (v) => { v = (v || "").trim(); return noteLabel.has(v) ? "see note (" + noteLabel.get(v) + ")" : v; };
  const rows = catRows.map(r => {
    const cite = (r[pcol("citation")] || "").trim();
    const loc  = (r[pcol("locator")]  || "").trim();
    return [r[pcol("parameter")], r[pcol("value")], r[pcol("units")],
            r[pcol("provenance_class")],
            (r[pcol("equation")] || "").trim() || "—",
            loc ? (cite ? cite + " — " + loc : loc) : cite,
            fold(r[pcol("sensitivity")])];
  });
  // `method_note` is deliberately NOT a column here. It is the internal working record of how
  // each value was established, written as a working note rather than as publication text. It is
  // retained in
  // data/parameters_provenance.csv and rendered for reading by data/export_method_notes.py into
  // docs/METHOD_NOTES_INTERNAL.md, both internal.
  s9.push(mkTable(["Parameter","Value","Units","State","Eq.",
                   "Citation with locator","Sensitivity / exposure"],
                  rows, [1700,900,600,900,600,3000,2300]));
  const st = { measured: 0, derived: 0, assumption: 0 };
  catRows.forEach(r => { st[r[pcol("provenance_class")]]++; });
  s9.push(cap("Table S7" + letters[i] + ". " + cat.replace(/^[0-9]+\. /, "") +
              " — " + rows.length + " entries: " + st.measured + " measured, " + st.derived +
              " derived, " + st.assumption + " assumption. Every measured entry carries a locator; " +
              "every assumption entry carries a sensitivity (§S9). Full strings for the shared " +
              "notes below are repeated on every applicable row of the machine-readable "  +
              "registry."));
  noteText.forEach(nt => s9.push(cap("(" + nt.L + ") [" + nt.n + " entries] " + nt.v)));
});

// ---- SUPPORTING FIGURES -------------------------------------------------------------------
// The SI referred to lettered figures 47 times -- §S6 alone 37 times, with panel-level
// detail -- and embedded NONE of them: word/media was empty in every build. A reader of S6 had
// 37 pointers to a figure that was not in the document. The renders existed on disk the whole
// time; nothing carried them into the .docx.
//
// They are collected here rather than interleaved because their intended inline positions are
// not recorded anywhere, and putting a figure in the wrong place is worse than collecting it.
// Supporting figures were removed on 2026-09-14 (author: "remove all the figures from the SI,
// we don't need them. This is a review/perspective."). Every lettered-figure reference in the
// prose and in the registry was re-pointed to the section that carries the analysis.


const back = [
  h1("S5. Stage 1: Nernst–Planck film model"),
  h2("S5.1 Formulation"),
  p("Within the film 0 ≤ x ≤ δ we solve, at steady state in dilute-solution theory, one conservation equation per species. The molar flux of species j is the Nernst–Planck expression (diffusion + migration; convection enters only through the film thickness δ that the reactor correlations set):"),
  eqn([{m:[msub("N","j"), mr("="), mr("−"), msub("D","j"), mfr([mr("d"), msub("c","j")], [mr("dx")]), mr("−"), msub("z","j"), mfr([mr("F")], [mr("RT")]), msub("D","j"), msub("c","j"), mfr([mr("dφ")], [mr("dx")])]}], "S3"),
  p("Conservation of mass for every species j, with the homogeneous EC′ source, is"),
  eqn([{m:[mfr([mr("d"), msub("N","j")], [mr("dx")]), mr("="), msub("ν","j"), mr("R"), mrb([mr("x")])]}, {t:",    j = 1, …, n"}], "S4"),
  p("where the single homogeneous step has the bimolecular rate law"),
  eqn([{m:[mr("R"), mr("="), mr("k"), msub("c","ox"), mrb([mr("x")]), msub("c","S"), mrb([mr("x")])]}], "S5"),
  p("with stoichiometric coefficients ν_ox = −1, ν_red = +1, ν_S = −1/(n_S·s_ox), and the proton/hydroxide partner of each system (Table S6) chosen so that the step conserves charge, Σ_j z_j ν_j = 0. Direct (non-mediated) electrolyses are the special case R = 0. The potential is closed by local electroneutrality, which replaces the Poisson equation at film scales vastly exceeding the Debye length:"),
  eqn([{m:[msum([msub("z","j"), msub("c","j"), mrb([mr("x")])], "j"), mr("="), mr("0")]}], "S6"),
  p("Conservation of charge is not imposed separately — it is a theorem of Eqs. S4–S6. Defining the ionic current density"),
  eqn([{m:[mr("i"), mrb([mr("x")]), mr("="), mr("F"), msum([msub("z","j"), msub("N","j"), mrb([mr("x")])], "j")]}, {t:",     "}, {m:[mfr([mr("di")], [mr("dx")]), mr("="), mr("F"), msum([msub("z","j"), msub("ν","j"), mr("R")], "j"), mr("="), mr("0")]}], "S7"),
  p("so the current entering at the electrode leaves the bulk face unchanged; this discrete statement is verified to machine precision (max face deviation 3×10⁻¹², §S5.6). Total mediator is likewise conserved: d(N_red + N_ox)/dx = (ν_red + ν_ox)R = 0. Boundary conditions:"),
  eqn([{m:[msub("N","j"), mrb([mr("0")]), mr("="), mfr([msub("s","j"), msub("i","app")], [mr("F")])]}, {t:"  with  "}, {m:[msum([msub("z","j"), msub("s","j")], "j"), mr("="), mr("1")]}, {t:";    "}, {m:[msub("c","j"), mrb([mr("δ")]), mr("="), msup(msub("c","j"), "bulk")]}, {t:",   "}, {m:[mr("φ"), mrb([mr("δ")]), mr("="), mr("0")]}], "S8"),
  p("the first being the galvanostatic electrode condition with electron-normalized stoichiometries (e.g., anodic oxidation of a neutral substrate releasing protons has s_S = −1/n and s_H+ = +1; a carboxylate anion substrate has s_S = −1 with z_S = −1; the 2 e⁻ quinone couple has s_red = −1/2, s_ox = +1/2, s_H+ = +1), and the second the Dirichlet bulk edge with the potential reference. The bulk Dirichlet condition on the oxidized mediator (its trace bulk value) is the perfect-sink idealization of a well-mixed reservoir; §S4 discusses when that idealization matters (ex-cell mediation)."),
  h2("S5.2 Numerics"),
  p("The film is discretized in N finite volumes (N = 80 for the Stage-1 verification cases (the §S5.3 support-ratio sweep ran at N = 60), N = 90 for EC′, on a geometric mesh whose first cell is matched to the reaction layer, dx₁ ≈ x_k/50 bounded by the uniform spacing; mesh-independence is demonstrated in §S5.6). The flux on the face between cells i and i+1 uses center-to-center spacing Δx_{i+½} and the arithmetic-mean concentration in the migration term:"),
  eqn([{m:[msub("N","j,i+1∕2"), mr("="), mr("−"), msub("D","j"), mfr([msub("c","j,i+1"), mr("−"), msub("c","j,i")], [mr("Δ"), msub("x","i+1∕2")]), mr("−"), msub("z","j"), mfr([mr("F")], [mr("RT")]), msub("D","j"), mfr([msub("c","j,i"), mr("+"), msub("c","j,i+1")], [mr("2")]), mfr([msub("φ","i+1"), mr("−"), msub("φ","i")], [mr("Δ"), msub("x","i+1∕2")])]}], "S9"),
  p("and the discrete statement of Eq. S4 integrated over cell i of width Δx_i is the flux balance actually solved,"),
  eqn([{m:[msub("N","j,i−1∕2"), mr("−"), msub("N","j,i+1∕2"), mr("+"), msub("ν","j"), mr("k"), msub("c","ox,i"), msub("c","S,i"), mr("Δ"), msub("x","i"), mr("="), mr("0")]}], "S10"),
  p("with the electrode face flux replaced by the boundary condition of Eq. S8 in the first cell and a bulk ghost value at half-spacing beyond the last cell. The unknowns are the logarithms of the nodal concentrations, u_j,i = ln c_j,i — enforcing positivity by construction — plus the nodal potentials, exactly as in the catalyst-layer model from which this solver derives.«bui2022» One residual row per species per cell is Eq. S10, row-scaled by D_j·max(C_j,bulk, 0.01·C_max, max_x c_j)/δ, and one row per cell is Eq. S7 (scaled by C_max). The last term in the row scale is the species' largest concentration in the current iterate. It is included so that an electrogenerated species that is a trace in the bulk but molar at the electrode is held to the same relative tolerance as the others: the oxidant of the chloride system is seeded at " + Number(EX.inputs.c_OX_bulk_molm3.toPrecision(2)) + " mol m⁻³ in the bulk (" + sciD(EX.inputs.c_OX_bulk_molm3 / (EX.inputs.C_Cl_M * 1000)) + " of the chloride concentration, the trace seed of Table S7e) and reaches " + EX.c_OX_at_limit_M.toFixed(1) + " M of oxidizing equivalents (" + (EX.c_OX_at_limit_M / 2).toFixed(1) + " M as Cl₂ or HOCl) at its carrier limit. Without the last term its reference concentration is the 1% floor, " + XC.cref.toFixed(0) + " mol m⁻³, about " + XC.ratio.toFixed(0) + " times below the concentration it reaches; on the " + EX.delta_um.toFixed(0) + " µm film, whose first cell is " + XC.dx1_um + " µm, its first-cell flux terms are then of order " + sciD(XC.terms) + " in scaled units, so the 10⁻⁹ tolerance asks for a relative accuracy of " + sciD(1e-9 / XC.terms) + " on them, the double-precision floor, and the concentration-control walk stops on a branch that exists. Table S7k gives the size of that effect. The nonlinear system F(u) = 0 is solved by damped Newton iteration,"),
  eqn([{m:[mr("J"), mr("Δu"), mr("="), mr("−"), mr("F"), mrb([mr("u")])]}, {t:",    "}, {m:[mr("u"), mr("←"), mr("u"), mr("+"), mr("λ"), mr("Δu")]}, {t:",    "}, {m:[mr("λ"), mr("∈"), mr("(0, 1]")]}], "S11"),
  p("with a dense forward-difference Jacobian, a log-step clamp (|Δu|∞ ≤ 2–3) to suppress nullspace amplification of the concentration block, backtracking line search on ‖F‖∞, and a Levenberg–Marquardt fallback (JᵀJ + 10⁻¹⁰I) on singular Jacobians. Galvanostatic operation is imposed through the boundary stoichiometry. The applied current is ramped with warm starts (natural continuation) only far enough to obtain a safe state, because that parameterisation has a fold at the limiting current and cannot cross it; the limiting current itself is then obtained by concentration control, prescribing the electroactive species' surface concentration and solving for the current until that surface concentration stops falling; §S5.5 reports the plateau each cell reaches, of which " + CENSUS.ncoll + " reach the collapse criterion c_red(0)/C_red < 10⁻³."),
  h2("S5.3 Supporting-electrolyte limits"),
  p("Two analytic limits constrain the implementation. With a neutral substrate under a fifty-fold excess of supporting electrolyte the computed plateau reproduces Eq. S1 to 0.1% (i_lim/i_Fick = 1.000). The production solve of the fifty-reaction layer uses a coarser first cell, and there the same neutral limit reads " + NP_NEUT.pct + "% high in every one of its " + NP_NEUT.n + " neutral cells, because the collapse criterion is tested at the first cell centre rather than at the wall; no neutral cell lies within that margin above 25 or 50 mA cm⁻², so no count moves. With an anionic substrate in a binary electrolyte and no added support, the computed plateau reproduces Newman's classical migration result«newman» i_lim = 2FDC/δ exactly (2.000 computed; the factor 2 is independent of the counter-ion diffusivity). Between these limits the migration enhancement decays from 2.00 through 1.38, 1.18, and 1.04 at support ratios of 0.25, 1, and 5, and the film potential drop collapses from ~57 mV to ~1 mV. For neutral substrates the Stage-0 and Stage-1 values agree to within a few percent at any support ratio; Table S5 reports the Stage-1 values throughout."),

  h2("S5.4 EC′ reaction–diffusion model for mediated electrolysis"),
  p("Treating a mediator as a species that merely commutes across the film understates its ceiling whenever the homogeneous step is fast. We therefore extend the film model to the full EC′ problem: the electrode exchanges electrons only with the mediator couple (s_red = −1, s_ox = +1), the substrate carries no electrode flux, and the bimolecular source of Eq. S5 (consuming Med_ox and S, regenerating Med_red) enters every finite-volume balance (Eq. S10). The analytic reference quantities used throughout are the reaction-layer thickness, the commuting (shuttle) bound, the Savéant catalytic current,«saveant» and the total-catalysis cap:"),
  eqn([{m:[msub("x","k"), mr("="), msq([mfr([msub("D","ox")], [mr("k"), msub("C","S")])])]}], "S12"),
  eqn([{m:[msub("i","shuttle"), mr("="), mfr([mr("F"), msub("D","red"), msub("C","med")], [mr("|"), msub("s","red"), mr("|"), mr("δ")])]}], "S13"),
  eqn([{m:[msub("i","Savéant"), mr("="), msub("n","c"), mr("F"), msub("C","med"), msq([msub("D","ox"), mr("k"), msub("C","S")])]}], "S14"),
  eqn([{m:[msub("i","cap"), mr("="), mfr([msub("n","S"), mr("F"), msub("D","S"), msub("C","S")], [mr("δ")])]}], "S15"),
  p("valid in the regimes δ/x_k ≪ 1, 1 ≪ δ/x_k ≪ γ, and δ/x_k ≫ γ respectively, where γ = D_S C_S / (D_med C_med) is the substrate/mediator transport ratio. At finite amplification the Savéant expression overpredicts because the reaction layer sees partially depleted substrate; the first-order correction, which is verified to ~1%, is"),
  eqn([{m:[mr("i"), mr("="), msub("i","Savéant"), msq([mr("1"), mr("−"), mfr([mr("A")], [mr("γ")])])]}, {t:",    "}, {m:[mr("A"), mr("="), mfr([mr("i"), mr("δ")], [mr("F"), msub("D","med"), msub("C","med")])]}], "S16"),
  p("Both diffusivities in those two groups are declared constants for the base case of §S5.4 (Table S7d: "
     + "D_med = " + sciX(EP.base.D_med) + " and D_S = " + sciX(EP.base.D_S)
     + " m² s⁻¹), so the regime boundaries of that base case inherit the "
     + "choice and we state what it costs. Setting δ/x_k = 1 and δ/x_k = γ gives "
     + "the two crossing rate constants k₁ = D_ox/(C_Sδ²) and "
     + "k₂ = γ²k₁, so the boundaries do not move "
     + "together: the shuttle/kinetic boundary scales as the mediator diffusivity and is independent of D_S, while "
     + "the kinetic/total-catalysis boundary scales as D_S²/D_med and is the more exposed of "
     + "the two. Over ±" + Math.round(100 * EP.band) + "% on both diffusivities — the "
     + "working property error of §S3.1 — the base case's boundaries move by at most "
     + EP.base.worst_span_decades.toFixed(2) + " decades in k, while the three rate constants of §S5.4 (k = "
     + EP.base.figH_k.map(function (k) { return k >= 100 ? "10" + String(Math.round(Math.log10(k))).replace(/\d/g, function (c) { return "⁰¹²³⁴⁵⁶⁷⁸⁹"[+c]; }) : String(k); }).join(", ")
     + " M⁻¹ s⁻¹) sit " + EP.base.figH_margin_decades.map(function (m) { return m.toFixed(2); }).join(", ")
     + " decades from the nearest boundary"
     + (function () {
         var inside = EP.base.figH_k.filter(function (k, i) { return EP.base.figH_margin_decades[i] < EP.base.worst_span_decades; });
         if (inside.length === 0) return ", so the regime each of those panels illustrates survives the declared values. ";
         return ": the k = " + inside.map(function (k) { return k >= 100 ? "10" + String(Math.round(Math.log10(k))).replace(/\d/g, function (c) { return "⁰¹²³⁴⁵⁶⁷⁸⁹"[+c]; }) : String(k); }).join(" and ")
           + " case" + (inside.length > 1 ? "s sit" : " sits") + " inside that movement and illustrate" + (inside.length > 1 ? "" : "s")
           + " the kinetic regime at the declared values only, the other" + (inside.length > 1 ? "" : "s") + " survive" + (inside.length > 1 ? "s" : "") + " them. ";
       })()
     + "The three rows drawn in main-text Fig. 6d–f — " + ["Bromination", "ACT", "NHPI"].map(function (s) {
         var r = EP.rows[s]; return (s === "Bromination" ? "the bromide-mediated bromination of anisole" : s === "ACT" ? "ACT-mediated alcohol oxidation" : "NHPI-mediated allylic C–H oxidation")
           + " (k = " + kSI(r.k_M)
           + " M⁻¹ s⁻¹, " + (r.regime_solved === "substrate-limited" ? "substrate-limited: the substrate is exhausted at the wall and the current falls back to the mediator's own transport, which Table S6 therefore lists as the limiter" : r.regime_solved === "mixed" ? "mixed control" : r.regime_solved) + ")"; }).join(", ")
     + " on the " + EP.rows.ACT.delta_um.toFixed(1) + " µm ANEC film — carry their own diffusivities (Table S6) and reach i_lim = "
     + ["Bromination", "ACT", "NHPI"].map(function (s) { var v = EP.rows[s].ilim_mAcm2; return v >= 100 ? v.toFixed(0) : v.toFixed(1); }).join(", ").replace(/, ([^,]*)$/, " and $1")
     + " mA cm⁻², with " + ["Bromination", "ACT", "NHPI"].map(function (s) { return (100 * EP.rows[s].share_in_film).toFixed(0) + " %"; }).join(", ").replace(/, ([^,]*)$/, " and $1")
     + " of the activated mediator consumed inside the film; their regime labels are assigned from the "
     + "solve rather than from these inequalities: substrate-limited when the substrate is exhausted at the wall; otherwise by the share of the "
     + "activated mediator consumed inside the film, mediator-limited below one third, kinetic above two thirds and mixed control between "
     + "(for a first-order step that share is 1 − 1/cosh(δ/x_k), so the two limits are δ/x_k = 0.96 and 1.76). Each label agrees with the analytic assignment, and "
     + "re-solving every row with D_med and D_S scaled in turn by " + (1 - EP.band).toFixed(2) + " and " + (1 + EP.band).toFixed(2)
     + (EP.labels_survive ? " leaves all three labels unchanged" : (function () {
         throw new Error("G-ECPANEL: a Fig. 6d-f regime label moves under the diffusivity band; rewrite this sentence, do not print it"); })())
     + "; the rate constants sit " + ["Bromination", "ACT", "NHPI"].map(function (s) { return EP.rows[s].margin_decades.toFixed(2); }).join(", ")
     + " decades from their nearest analytic boundary, which itself moves by up to " + EP.rows_worst_span_decades.toFixed(2)
     + " decades across the band — the reason the labels are re-solved rather than read off the inequalities."
     + ""),
  p("Because x_k shrinks to sub-micrometer scale at large k, the film is discretized on a geometric mesh with the first cell matched to x_k as described in §S5.2."),
  p("The solver reproduces the three analytic regimes. As k → 0 the plateau recovers the commuting bound F·D_med·C_med/δ to within the tolerance §S5.6 reports. At intermediate k the computed plateau tracks the Savéant catalytic current F·C_med·(D_med·k·C_S)^1/2 with the correct half-order slope, reaching a thirty-six-fold amplification over the commuting bound at k = 10³ M⁻¹ s⁻¹, by which point the base case has passed into total catalysis and sits just under its substrate cap (20 mM mediator, 0.5 M substrate, δ = 100 μm, D_med = 6 × 10⁻¹⁰ m² s⁻¹, D_S = 1 × 10⁻⁹ m² s⁻¹; the two diffusivities are declared constants with no source, registered as assumptions in Table S7d, and the substrate cap F·D_S·C_S/δ = 48.24 mA cm⁻² and the commuting bound F·D_med·C_med/δ = 1.16 mA cm⁻² follow from them, as does γ = D_S·C_S/(D_med·C_med) = 41.67). At larger k still, the system enters total catalysis: the substrate is exhausted inside the film, the reaction zone detaches from the wall, and the plateau saturates at F·D_S·C_S/δ — numerically identical to the ceiling the same substrate would have in a direct electrolysis. Detecting this regime correctly requires the plateau criterion to watch the electroactive species (Med_red starvation at the electrode), not the substrate, whose surface collapse is a feature of the regime rather than its end. Once x_k falls to about 1 μm (k ≈ 1.2 × 10³ M⁻¹ s⁻¹ here) the steady state develops a reaction front in mid-film; in the production cells that reach that regime concentration control resolves it (§S5.5), and for this base case the exact total-catalysis limit is the reference. The regime assignments this base case supports are stated as regime statements and not as scale-invariant ones. Sweeping each diffusivity over ×1/3 to ×3 leaves the k → 0 shuttle result unchanged — the plateau recovers the commuting bound to within 1–8% in every case, and is exactly independent of D_S — but the regime that any fixed k occupies does move, because x_k ∝ √D_med and γ ∝ D_S/D_med: at k = 10³ M⁻¹ s⁻¹ a threefold larger D_S carries the system out of total catalysis and back into the Savéant regime. What is invariant is the existence and ordering of the three regimes and their selection by δ/x_k and γ, which is what §S5.4 claims; each case reports the x_k, δ and inequality that certify its own label."),
  p("The design consequence sharpens the main-text argument. The Stage-0 values of the mediated rows (Table S6) are floors that apply when homogeneous kinetics are slow; a mediator with k ≳ 10³ M⁻¹ s⁻¹ at 0.5 M substrate erases the mediator-transport penalty entirely, making the mediated ceiling indistinguishable from the substrate-carried one while retaining the selectivity benefits of indirect electrolysis. Fast mediator kinetics thus substitute for convection inside the film — a chemical analogue of reactor engineering. The same amplification is available in principle to a dilute molecular catalyst whose cycle closes at one electrode, which the model treats with the same EC′ formalism as a mediator; the published matrix carries " + (SR ? numWordCap(SR.n_sourced).toLowerCase() : "none") + " of the " + numWord(N_CAT) + " at a rate constant measured (nickel) or estimated by voltammetric simulation (cobalt hydride) on a related system, and the other " + (SR ? numWordCap(SR.n_floor).toLowerCase() : numWord(N_CAT)) + " at the k = 0 floor, and §S5.7 measures what a faster cycle would buy: up to " + ckAmp.toFixed(1) + "× in a single cell (" + CK_AMP_TXT + ") and " + CK_BEST.gain.toFixed(0) + "× on a row's best-architecture ceiling (" + CK_BEST.row + "), and the dilute substrate caps what any faster cycle could add."),

  h2("S5.5 Mediated entries"),
  p("Every mediated entry of the 50-reaction set was re-solved with the complete EC′ treatment of §S5.4 — mediator generation at the electrode boundary condition, both mediator forms and the substrate transported through the Nernst–Planck/electroneutrality system, and consumption coupled in every film cell by the explicit homogeneous source term R = k·c_ox·c_S — across all " + ARCH.length + " reactor archetypes (" + (N_MED * ARCH.length) + " solves). Electron bookkeeping: electrode stoichiometries s_j are per electron (s_red = −1/n_c per mediator molecule; a proton-releasing couple such as H₂Q/BQ carries the balance of charge through an explicit H⁺ species), and the homogeneous stoichiometry consumes ν_S = −1/(n_S·s_ox) substrate per oxidant event. The Cl₄NHPI mediator is carried as the deprotonated anion in both layers (Table S2, as the exemplar's pyridine conditions make it), with pyridinium as its counter-cation and the proton the homogeneous step returns, so its published cells credit the anion's migration, which raises the k = 0 ceiling by a factor of " + NHPI_MIG.toFixed(2) + " in every architecture. The same row passes both anodic electrons of each enone through the N-oxyl. The exemplar's mechanism spends the second on the tert-butylperoxyl radical, which it describes as electrochemically generated from tBuOOH without saying whether at the anode or by the N-oxyl «horn2016»; the model takes the second reading, under which the mediator carries the whole current. Homogeneous rate constants are order-of-magnitude, literature-anchored estimates (Table S6); the conclusions are regime placements through x_k = (D_ox/kC_S)^1/2 and are robust on a log scale. Every specification is checked at runtime against the model's conservation laws before any solve: |Σ z_j·s_j| = 1 (the electrode stoichiometry, +1 anodic and −1 for the one cathodic entry), Σ z_j·ν_j = 0 (the homogeneous step must conserve charge — proton- or hydroxide-coupled partners are explicit species — so that ∇·i = 0 holds across the film), and bulk electroneutrality. The collapse detector watches the electroactive reduced species only — substrate surface collapse is a feature of total catalysis and of dilute-substrate systems, not a terminal state — and the reported i_lim is reached by concentration control rather than quantized by the ramp step. The first mesh cell is matched to the reaction layer (dx1 ≈ x_k/50, bounded by the uniform spacing) per §S5.6. Ramping the current cannot cross the limiting current: dc_surf/di → −∞ there, so the Jacobian degenerates exactly at the answer and Newton fails just short of it. The ramp is therefore used only to reach a safe state, and the reported value comes from concentration control — the reduced-mediator surface concentration is prescribed and the current solved for as an unknown, which is monotone through the fold. Of the " + CENSUS.nall + " mediated cells, " + CENSUS.n + " end on a plateau of this walk, where the current no longer responds to further depletion: the reduced mediator there sits between " + CENSUS.lo + "% and " + CENSUS.hi + "% of its bulk value, " + CENSUS.ncoll + " of them reaching the 10⁻³ criterion exactly, " + CENSUS.n028 + " of the " + CENSUS.n + " at or below 0.28%. " + plateauSentence() + " " + WALL_SENT + " record a Newton wall from the ramp that preceded concentration control, and the walk that followed did not rise above their k = 0 floor, so the value published is that floor: the oxazole row is carried at k = 0, so its floor is its solution, and in the three thinnest films the ethylene epoxidation sits at the chloride's migration-limited ceiling, which its dissolved ethylene could raise by at most " + WALL_ETH_ADD + "%. Doubling the mesh and refining the continuation 7.5-fold together (N = 90 → 180, growth 1.15 → 1.02) move the answer by at most " + G12_TXT + "% on the two rows re-solved at their production mesh. The cell that most tests this is the anisole bromination in an unstirred beaker, at its measured rate constant, with δ/x_k = " + Math.round(BROM_UN.delta / BROM_UN.xk) + ": the substrate is exhausted at the wall and the reaction front detaches into the interior, leaving a dead zone in which the substrate falls to " + SUP(BROM_CSUB) + " of bulk at the wall. The ordinary walk reaches it by concentration control and resolves it at " + BROM_UN.ec.toFixed(1) + " mA cm⁻², " + ecAmp(BROM_UN).toFixed(2) + " times the cell's own commuting bound of " + BROM_UN.t0.toFixed(2) + " mA cm⁻²: the bromide's migration lift (§S5.5) and almost nothing besides, because the anisole, at " + Math.round(BROM_COX.cs) + " mM against " + Math.round(BROM_COX.cm) + " mM of bromide, can return little of it. One caveat belongs with that number: sustaining a front that the model places no farther than x_f ≈ " + Math.round(BROM_XF_MAX / 5) * 5 + " µm from the electrode (the substrate it consumes crosses δ − x_f, which bounds x_f by δ(1 − i_cap/i_ec), with i_cap the substrate cap) requires the bromine made at the anode to accumulate between the electrode and the front, fed by migration of Br⁻ into the anode; on the ANEC film of main-text Fig. 6d it reaches " + BROM_COX.M.toFixed(2) + " M, " + BROM_COX.ratio.toFixed(1) + " times the bromide bulk. The Nernst–Planck system is satisfied exactly, but the model carries no Br₂ solubility ceiling and no Br₃⁻ speciation, so whether the chemistry supports such a front at " + BROM_UN.delta.toFixed(0) + " µm is outside what this model can answer. Every cell published from that walk ends on such a plateau, so none of them is a bound that further solver refinement could move; the ten published at their k = 0 floor are bounded as described above. The practical consequence of the remaining imprecision is measured rather than argued. Replacing every solved mediated value by its closed-form envelope min(Savéant, substrate supply), and separately by its Stage-0 floor, brackets the reported counts at ≥25 mA cm⁻² between " + bracket().text + " of 50, and the architecture ordering " + ORDERING_TEXT + " is preserved at both ends. Neither endpoint is a bound: " + bracket().above + " of the " + bracket().nFin + " finite-k solves already sit above min(Savéant, substrate supply) — " + bracket().aboveCap + " of them above the substrate-supply term itself. That planar cap assumes the reaction front sits at the electrode: in " + bracket().exh + " of those cells the substrate is exhausted at the wall and the front has left it; in " + bracket().near + " more (" + bracket().nearRows + ") it is not exhausted at the wall (" + (100 * bracket().nearLo).toFixed(1) + "–" + (100 * bracket().nearHi).toFixed(0) + "% of bulk) but reacts within the film, over a zone that widens as the substrate is depleted (x_k = " + bracket().xkLo.toFixed(1) + "–" + bracket().xkHi.toFixed(1) + " μm at bulk concentration), so it diffuses less than δ and its supply exceeds the planar cap; these cells are still substrate-limited, and a tenfold larger k raises their current by at most " + Math.ceil(100 * bracket().up10) + "%. " + (bracket().kinN ? (bracket().kinN === 1 ? "One more, " : numWordCap(bracket().kinN) + " more, ") + bracket().kinCells + (bracket().kinN === 1 ? ", sits" : ", sit") + " above the cap without being held there: a tenfold larger k raises " + (bracket().kinN === 1 ? "it" : "them") + " by " + (bracket().kinN === 1 ? "" : "at least ") + Math.floor(100 * bracket().kinUp) + "%, as it would a kinetic cell. " : "") + "In the other " + bracket().mig + " (" + bracket().migRows + ") the carrier migrates in its own salt at about twice its Fick bound and carries the current past the cap. It is a perturbation of comparable size, not an envelope, and not a cap. The integers in Table S5 should be read with that band; the ranking does not depend on it. The bracket is recomputed in both directions from the two matrices at build time, so this sentence cannot state a range its own model does not give."),
  mkTable(["Mediated system","k (M⁻¹s⁻¹)","k provenance (order-of-magnitude)","x_k (μm)","stirred: Stage-0 → EC′ (mA/cm²)","ANEC: Stage-0 → EC′","limiter at i_lim","EC′, unstirred → rotating cylinder (gain)"],
    s6FromMatrix([["Br⁻ / Hofmann rearrangement (80 mM, MeCN)","10³","N-bromination of the amide N–H by anodically generated bromine, the first step of the rearrangement.«wallis1946» Set at the constant for aqueous HOBr with propionamide (measured by Pattison and Davies and compiled by Heeb et al.), the unbranched primary amide nearest the exemplar's 2-phenylacetamide: 3.3 M⁻¹ s⁻¹ (apparent, pH 7.2–7.5, 22 °C), with 2-methylpropionamide at 1.5 and trimethylacetamide at 0.9 under the same conditions, five to six decades below amines and sulfamides.«heeb2014» The exemplar differs from the measurement in its oxidant (molecular bromine), its medium (MeCN, with base generated at the cathode, hydroxide per the exemplar, and part of the bromine held as Br₃⁻ at this bromide loading) and its temperature (near 50 °C against the model's isothermal 25 °C); the tenfold perturbation of §S5.5 shows what a decade either way would move, while the transfer itself is not bounded","2.3","21 → 335","55 → 889","≥ (Newton-wall lower bound)"],
     ["ACT / alcohol oxidation (25 mM, aq. pH 8.5)","20","oxoammonium + primary alcohol. The mediator's measured turnover with four primary alcohols in 1:1 water/acetonitrile carbonate buffer, 659–1703 h⁻¹ at 20 mM alcohol«rafiee2018» (400–1900 h⁻¹ as the exemplar quotes it«zhong2021»), is 9–24 M⁻¹ s⁻¹ read as a pseudo-first-order constant; the step is base-assisted«bailey2007» and the exemplar, which runs at pH 8.5, reports a lower rate on lowering the pH.«zhong2021» Each turnover removes two electrons from the alcohol, while the model books one event per electron the oxoammonium carries, so in the model's convention the same turnovers give 18–47 M⁻¹ s⁻¹; 20 is a declared order of magnitude at the bottom of that range, and the kinetic plateau, which scales as k^½, would be up to 1.5 times higher at its top","7.7","1.4 → 17","6.3 → 18","mediator plateau (≥ in weak reactors)"],
     ["Cl⁻ / ethylene epoxidation (1 M KCl, aq.)","10","HOCl with twelve other olefins (nine cinnamic-acid derivatives and three aliphatic olefins) 4.5 × 10⁻³–19 M⁻¹ s⁻¹, and Cl₂ with two of them 4.2 × 10⁴ and 1.1 × 10⁶;«livongunten2020» with three ionones, HOCl 12–165 and Cl₂ 6.3 × 10⁷–2.7 × 10⁸.«lau2019» Not measured for ethylene; declared inside the HOCl range. The ceiling is k-independent: i_lim is carrier/migration-limited, and the chloride an in-film reaction can return to the electrode is capped by the ethylene flux at any k (§S5.5)","157","392 → 789","1145 → 2305","carrier (migration ×2.0)"],
     ["Cl₄NHPI / allylic C–H (33 mM, acetone)","20.2","hydrogen abstraction from an allylic C–H by the N-oxyl. Measured for the parent radical: electrogenerated PINO with cyclohexene in MeCN with pyridine, 20.2 M⁻¹ s⁻¹ (allylic substrates 12.8–77.6; ethylbenzene 1.85).«ueda1987» The exemplar cites that study and, from its own voltammetry, expects the tetrachloro radical to be the more reactive;«horn2016» see also Nutting, Rafiee and Stahl«nutting2018» and Yang et al.«yang2023»","158","6.7 → 7.6","19 → 20","mediator (kinetics-limited)"],
     ["ACT / HMF → FDCA (40 mM, aq. pH 10)","50","oxoammonium + the hydroxymethyl and formyl groups of HMF at pH 10. Not measured for HMF: the mediator's turnover with primary alcohols and aldehydes in 1:1 water/acetonitrile carbonate buffer (the ACT entry's conditions), 246–1921 h⁻¹ at 20 mM,«rafiee2018» is 3–27 M⁻¹ s⁻¹ read as above and 7–53 in the model's one-electron convention, and the exemplar reports the activity qualitatively (rising with pH to 10; ACT⁺ faster than TEMPO⁺).«cardiel2019» Declared order of magnitude at the top of that range; nitroxyl-mediated HMF oxidation in other media: Vo et al.«vo2024»","10.9","2.3 → 18","10 → 21","≥ (Newton-wall lower bound)"],
     ["BQ / Wacker–Tsuji (22 mM, MeCN/H₂O)","0.06","regeneration of palladium by benzoquinone, written as the alkene-dependent rate it caps. Benzoquinone does not react with the alkene; it is consumed only when it reoxidizes Pd(0), so the hydroquinone can be returned no faster than the palladium turns over. The exemplar's own Pd(OAc)₂ (1.1 mM) turns over at 0.025 s⁻¹ at its maximum electrolysis current and at 0.14 s⁻¹ with stoichiometric benzoquinone (1-decene, MeCN/H₂O 7:1),«miller1992» which written as k·C_BQ·C_S gives k ≤ 0.14 × 1.1 mM/(22 mM × 0.11 M) = 0.06 M⁻¹ s⁻¹; the upper value is adopted. The exemplar attributes the reoxidation to inner-sphere electron transfer within a protonated Pd(0)–benzoquinone complex;«miller1992» the acid-induced conversion of Pd(0)–benzoquinone complexes to Pd(II) and hydroquinone is shown independently by Grennberg, Gogoll and Bäckvall«grennberg1993»","12.7","7.6 → 28","23 → 50","≥ (Newton-wall lower bound)"],
     ["Br⁻ / electrophilic bromination (0.25 M, aq./MeCN)","2.28 × 10⁴","Br₂ + anisole, measured for this carrier and this substrate in water at 20 °C: (2.23 ± 0.14) × 10⁴ M⁻¹ s⁻¹ at the para position and (5.4 ± 0.6) × 10² at the ortho position«sivey2015» (Br₂ ≈ BrOCl < BrCl, five decades above HOBr). The sum is adopted; the exemplar's medium is mixed aqueous–organic","3.2","50 → 111","145 → 320","substrate cap (unstirred, RDE, RCE); ≥ elsewhere"],
     ["SCN⁻ / thiocyanation (0.1 M, AcOH/HCOOH)","10²","(SCN)₂ + arene, ArH + (SCN)₂ → ArSCN + SCN⁻ + H⁺ (2 e⁻/ArH): NO direct rate measurement located — estimate by analogy to halogenation (least-constrained entry); thiocyanogen aqueous formation/hydrolysis kinetics: Nagy, Lemma and Ashby;«nagy2007» anodic thiocyanation: Gitkis and Becker«gitkis2010»","4.7","7.5 → 18","30 → 61","mediator / ≥ (mixed)"],
     ["Br⁻ / amidyl C–H amination (40 mM, MeCN/MeOH)","10³","N-bromination of an amide N–H by anodically generated bromine, the step of the Hofmann entry; value carried over from that row, the constant for HOBr with propionamide measured by Pattison and Davies and compiled by Heeb et al.,«heeb2014» as a transfer for the same step. The exemplar assigns the step: bromine 'is intercepted by the substrate' to give the N–Br amide that releases the amidyl radical«zhangxu2018»","","","","substrate (exhausted at the wall; bromide is the only electrolyte, so the carrier also migrates, ×2)"],
     ["Cl⁻ / thioether → sulfone (14 mM, MeCN/aq. HCl)","10³","No rate constant is printed for the oxidation of this thioether by electrogenerated chlorine species. The value is bounded from the exemplar's own operation on plate electrodes: 40 mA cm⁻² at 0.1 M thioether and 14 mM chloride, with conversion per charge independent of current density (20–40 mA cm⁻²) and of flow rate (125–500 mL min⁻¹),«bottecchia2022» requires k ≥ (i/F·C_med)²/(D_ox·C_S) = " + sci1(K_THIO) + " M⁻¹ s⁻¹; rounded up to the decade","","","","substrate cap (batch films); kinetic plateau elsewhere, raised where chloride migrates into the film"],
     ["O₂ / Giese addition (0.27 mM, aq./MeCN)","10³","No rate constant is printed for the step. The exemplar judges direct electron transfer from superoxide to the alkyl iodide unlikely and proposes a relay in which the hydroperoxyl radical reacts with hypoiodous acid to give the hydroxyl radical that activates the iodide,«liwilden2020» so the constant is an effective one for reduced oxygen, carried as HO₂• at the pH of the medium. It is bounded from the exemplar's own charge record: about 300 C over about 23 h (84 ks, Fig. 2) at one graphite rod of 4.12 cm², a time-averaged " + (GIESE_I / 10).toFixed(1) + " mA cm⁻², with air-saturated oxygen as the only electroactive species, requires k ≥ " + sci1(K_GIESE) + " M⁻¹ s⁻¹ (a quarter of that if both rods of the chamber are cathodes); rounded up to the decade. The charge passed, about 300 C for 1.2 mmol of product (2.6 F per mole of product; the exemplar quotes 2.4 F mol⁻¹ per mole of iodide), is 1.3 times the two electrons each product consumes; if the excess forms no product the bound is generous by up to a factor of about 1.7","","","","mediator (kinetic plateau; x_k ≪ δ in every film)"],
     ["Ar₃N / oxazole synthesis (5 mM, MeCN)","0","tri(p-tolyl)aminium radical cation + the enamide the ketone forms with acetonitrile and the anhydrides (single electron transfer; the second oxidation follows at the anode or by the aminium).«bao2022» No rate constant was located for an aminium with an enamide, and the exemplar runs on carbon felt at constant cell voltage, so its operation bounds nothing. Solved at k = 0, the mediator's own transport floor","","","","mediator (k = 0: the commuting bound)"]]),
    [2000,650,2800,550,1300,1200,1400,1200]),
  cap("Table S6. The mediated EC′ matrix (stirred batch and ANEC flow-cell columns shown, with the unstirred and rotating-cylinder ceilings and their ratio, the gain from intensification, in the last column; the full " + N_MED + "×" + ARCH.length + " matrix is solved). " + MED_SLOPE_SENT + " Stage-0 is the commuting bound F·D_med·C_med/(|s_red|·δ) — the k→0 floor; EC′ is the solver i_lim with the source term active. The limiter is read from the seven solved cells: the carrier, with its migration factor, where the current sits near twice its Fick bound in every film; the substrate where the solve exhausts it at the wall or the current reaches its planar supply cap n_S·F·D_S·C_S/δ; otherwise the mediator: transport-limited where its reaction layer x_k is thicker than δ, at its kinetic plateau where the current lies within 10% of n_c·F·C_med·(D_ox·k·C_S)^1/2, and otherwise below it, or above it by the factor stated."),
  p((() => {
    // the grouping this paragraph states, asserted against the record so the prose cannot outlive it
    const G = { "same carrier and substrate": ["Br- oxidation / electrophilic bromination"],
      "analogue of the carrier": ["NHPI-mediated allylic C-H -> enone", "Br-mediated Hofmann rearrangement", "Amidyl-radical C-H amination (phenanthridinone)"],
      "same carrier, other substrates": ["ACT-mediated alcohol oxidation (flow, hectogram)", "HMF -> FDCA (biomass)", "Cl-mediated ethylene epoxidation"],
      "bound from the exemplar's own data": ["BQ-mediated Wacker-Tsuji oxidation", "Thioether -> sulfone (kilo-scale)", "Cathodic Giese (R-I + alkene)"],
      "none measured": ["Aryl thiocyanation (NH4SCN)", "Oxazole synthesis from ketones and acetonitrile"] };
    const med = KBR.filter(r => r[kbc("carrier_class")] === "mediator");
    const named = Object.values(G).flat();
    if (named.length !== med.length || med.some(r => !(G[r[kbc("relation")]] || []).includes(r[kbc("reaction")])))
      throw new Error("the Table S6 k paragraph groups the mediated rows differently from rate_constant_basis.csv");
    if (kOf("Oxazole synthesis from ketones and acetonitrile") !== 0) throw new Error("the k paragraph says the oxazole row is solved at k = 0");
    return "The k column is a set of declared values, and Table S11 sets beside each one the system it was measured on. One entry carries a constant measured for its own carrier and substrate (bromine with anisole, in water). Three rest on measurements with the same or the parent carrier and other substrates: the allylic C–H oxidation on electrogenerated PINO with cyclohexene, and the two ACT entries on the mediator's turnover frequencies with primary alcohols and aldehydes, which are not second-order constants and fix the order of magnitude only. The chloride entry sits inside the range measured for HOCl with other olefins and is k-independent. Three entries are bounded by the exemplar's own operation. The Wacker–Tsuji constant is the palladium turnover the exemplar measures, written as the alkene-dependent rate it caps, because the hydroquinone is returned to benzoquinone only as fast as palladium consumes it. For the chloride-mediated thioether oxidation and the oxygen-mediated Giese addition the constant is the smallest one under which the kinetic plateau carries the current the exemplar itself reports on a smooth electrode of stated area, rounded up to the decade; for those two rows the constant is therefore a floor on k, not a measurement (the thioether row then runs at its kilogram campaign's concentrations, above the 0.1 M of the current density that fixed the bound), and what the solve adds is the reaction-layer thickness at the adopted constant (" + ecOne("Thioether", "Stirred batch").xk.toFixed(1) + " and " + ecOne("Giese", "Stirred batch").xk.toFixed(1) + " μm; " + (ecOne("Thioether", "Stirred batch").xk * Math.sqrt(1e3 / K_THIO)).toFixed(1) + " and " + (ecOne("Giese", "Stirred batch").xk * Math.sqrt(1e3 / K_GIESE)).toFixed(1) + " μm at the bounds themselves), thinner than every film, so neither row is limited by the transport of its mediator: " + thioGieseShape() + " Two rest on a measurement with a related brominating agent: the Hofmann N-bromination takes the constant measured for aqueous HOBr with propionamide, the unbranched primary amide nearest the exemplar's substrate, and the amidyl-radical amination inherits that value for the same step. Two entries have no measurement behind them: the thiocyanation value is an analogy to halogenation, and the triarylamine-mediated oxazole synthesis is solved at k = 0, the transport floor of its mediator, because nothing bounds its constant. ";
  })() + "Three statements bound the impact of these uncertainties. Two are structural: regime placement enters only as δ/x_k ∝ √k (log-scale robust), and the chloride entry's carrier-limited i_lim at its migration ceiling is k-independent, because the chloride an in-film reaction returns to the electrode is capped by the ethylene flux into the film, n F D C/δ for ethylene (" + ETH_BOUND.toFixed(2) + " mA cm⁻² at the stirred film, against a ceiling of " + matCell(ETH, "stirred").toFixed(0) + "), at any k from the HOCl pathway (≈10) to the fastest Cl₂ constants measured with an alkene in the two studies cited (6.3 × 10⁷–2.7 × 10⁸ M⁻¹ s⁻¹ for three ionones, Table S6). The oxidant partition of the propylene solve of §S4 is not k-independent and is reported for the HOCl pathway only. The third is measured rather than argued: perturbing each rate constant by a factor of ten in either direction, one row at a time, and re-solving the mediated matrix moves at least one cell across the 25 mA cm⁻² threshold on " + KS.summary.rows_crossing_25.length + " of the " + numWord(KS.summary.n_rows) + " rows solved at a finite rate constant" + (KS.summary.n_rows !== N_MED ? " (the row at k = 0 has no constant to move)" : "") + " — " + ksList() + " — so the ≥25 mA cm⁻² count of any single architecture moves by at most ±" + KS.summary.max_count_delta_25 + " and the ≥50 mA cm⁻² count by at most ±" + KS.summary.max_count_delta_50 + " from any one rate constant, " + (KS.summary.ordering_preserved ? "and the ordering the main text claims (unstirred below stirred below recirculating flow below the ANEC cell, the three thin-film archetypes above it) holds throughout" : "and the architecture ordering changes") + ". The rate constants are therefore the softest input behind the threshold status of those rows, and the counts in the main text should be read with that ±" + KS.summary.max_count_delta_25 + " in mind."),
  p("Three structural results. First, source-term coupling only raises mediated ceilings — amplifications run " + AMP_ALL + " over the commuting floor — so a commuting-carrier (Stage-0) treatment of these rows would understate them, and with the coupling active the stirred-beaker ≥50 mA cm⁻² count among mediated entries rises from " + ecCount("Stirred batch", 50, "t0") + "/" + N_MED + " to " + ecCount("Stirred batch", 50, "ec") + "/" + N_MED + " (≥25: " + ecCount("Stirred batch", 25, "t0") + "/" + N_MED + " to " + ecCount("Stirred batch", 25, "ec") + "/" + N_MED + "). The chloride/ethylene entry converges to 2.0× its Fick bound in every reactor — the analytic binary-electrolyte migration factor emerging from the full model — and the Hofmann system at its verified scale-up conditions (80 mM Br⁻ carrying 0.4 M substrate), at the constant measured for aqueous HOBr with propionamide, turns its mediator over in a " + HOF_ST.xk.toFixed(0) + " μm reaction layer, inside the two batch films and the recirculating flow film (δ/x_k ≈ " + Math.round(HOF_ST.delta / HOF_ST.xk) + " stirred), comparable to the ANEC film and wider than the " + HOF_THIN_NAMES + " films: the stirred beaker jumps from a " + Math.round(HOF_ST.t0) + " mA cm⁻² floor to " + Math.round(HOF_ST.ec) + " mA cm⁻² (×" + Math.round(ecAmp(HOF_ST)) + "), with the amide, five times the bromide, drawn down to " + (100 * HOF_ST_CS).toFixed(1) + " % of bulk at the wall but not exhausted, while in those thinner films the bromine leaves the film before it reacts and the row sits within " + Math.ceil(100 * Math.max(...HOF_THIN_K0)) + " % of the bromide's own migration-limited ceiling. Second, the dilute-nitroxyl systems (ACT at 25 and 40 mM, run respectively in a divided recirculating flow cell and a divided stirred cell) amplify strongly in batch (" + fRange(batchOf(ACT).concat(batchOf(HMF)).map(ecAmp), v => "×" + Math.round(v)) + ") yet land at nearly the same " + fRange(ACT.map(c => c.ec), v => String(Math.round(v))) + " and " + fRange(HMF.map(c => c.ec), v => String(Math.round(v))) + " mA cm⁻² in every reactor from beaker to RCE: fast kinetics substitute for convection, the reaction layer is thinner than every fixed film of Table S1, and the remaining levers are C_med and k — the mediated plateau of the payoff map made concrete, the quantitative explanation for why flow chemistry alone did not push these systems over the barrier, and precisely why the 200-g levetiracetam campaign«zhong2021» engineered around the plateau with a three-dimensional graphite-felt anode (100 cm² geometric) in a divided recirculating flow cell: it ran at 300 mA cm⁻² of geometric current density at pH 8.5, carried by the felt's internal area, which a planar film does not credit, so that figure is not comparable with the planar ceilings here. Third, the Cl₄NHPI system changes regime inside the range of films: with hydrogen-atom abstraction at k ≈ " + kSI(kOf("NHPI-mediated allylic C-H -> enone")) + " M⁻¹ s⁻¹ the reaction layer (x_k ≈ " + Math.round(NHPI[0].xk) + " μm) is thinner than the batch and recirculating-flow films, where regeneration inside the film lifts the ceiling " + fRange(NHPI_THICK.map(ecAmp), v => "×" + v.toFixed(1)) + " above the transport floor to a kinetic plateau of " + fRange(NHPI_THICK.map(c => c.ec), v => String(Math.round(v))) + " mA cm⁻², and thicker than the microfluidic and rotating-electrode films, where the activated mediator leaves before it reacts and the ceiling is the mediator's own transport bound (" + fRange(NHPI_THIN.map(ecAmp), v => "×" + v.toFixed(2)) + "); the ANEC film sits between (×" + ecAmp(NHPI_ANEC).toFixed(1) + ")."),
  p((() => {
    const G = ecRows("Cathodic Giese"), TH = ecRows("Thioether"), AM = ecRows("Amidyl");
    if (G.length !== ARCH.length || TH.length !== ARCH.length || AM.length !== ARCH.length) throw new Error("S5.5: a mediated row is missing cells");
    const csub = (c) => { const m = /c_sub\/cb ([0-9.eE+-]+)/.exec(c.limiter); if (!m) throw new Error("no c_sub/cb on " + c.rxn + "/" + c.reactor); return Number(m[1]); };
    const accum = (c) => c.ec / (c.sav * Math.sqrt(csub(c)));       // oxidant at the electrode / bulk mediator, from i = F c_ox(0) (D k c_S(0))^1/2
    const thA = ecOne("Thioether", "ANEC flow cell"), thM = ecOne("Thioether", "Microfluidic cell (25 um gap)"), thU = ecOne("Thioether", "Unstirred batch");
    const thTop = TH.reduce((a, c) => (c.ec > a.ec ? c : a), TH[0]);
    if (thTop !== thA) throw new Error("S5.5 says the thioether ceiling peaks on the ANEC film; the matrix says " + thTop.reactor);
    if (!(accum(thA) > 1.5 && accum(thA) > accum(thM))) throw new Error("S5.5: the oxidant accumulation that explains the thioether maximum is not in the matrix");
    const amU = ecOne("Amidyl", "Unstirred batch");
    // 2026-10-07: at the Hofmann constant (3.3 M-1 s-1) the amidyl reaction layer is thinner than the batch films only
    const AMDC = (c) => { const m = /c_sub\/cb ([0-9.eE+-]+)/.exec(c.limiter); return m ? Number(m[1]) : NaN; };
    const AMD = ecRows("Amidyl"), AMDB = AMD.filter(c => /batch/.test(c.reactor)), AMDO = AMD.filter(c => !AMDB.includes(c));
    const AMDK0 = Math.max(...AMDO.map(c => c.ec / npK0(c.rxn, c.reactor) - 1));
    if (AMDB.length !== 2 || AMDB.some(c => c.xk >= c.delta || !(AMDC(c) > 0.05 && AMDC(c) < 0.5)) || AMDO.some(c => c.xk < c.delta) || !(AMDK0 < 0.35))
      throw new Error("S5.5: the amidyl sentence no longer matches the matrix: " + AMD.map(c => c.reactor + " " + c.xk + "/" + c.delta + " " + AMDC(c)).join("; ") + " k0 " + AMDK0);
    return "Three further entries sit at the edges of these regimes. The oxygen-mediated Giese addition is the extreme kinetic case: its carrier is dissolved oxygen at " + CARR_mM.get("Cathodic Giese (R-I + alkene)").toFixed(2) + " mM, the reaction layer is " + G[0].xk.toFixed(1) + " μm, and the ceiling is " + fRange(G.map(c => c.ec), v => v.toFixed(1)) + " mA cm⁻² in every architecture, the lowest in the set — the supply of the aerial mediator, not the film, sets the rate. The chloride-mediated thioether oxidation runs at " + fRange(TH.filter(c => c.delta < 20).map(c => c.ec / thA.sav), v => v.toFixed(2)) + " times its Savéant plateau of " + Math.round(thA.sav) + " mA cm⁻² on the thin films, the excess coming from chloride migration, and is substrate-capped on the batch films (" + Math.round(thU.ec) + " mA cm⁻² unstirred against a planar substrate cap of " + Math.round(thU.cap) + "). Between the two its ceiling passes through a maximum of " + Math.round(thA.ec) + " mA cm⁻² on the ANEC film rather than rising to the thinnest: the potential drop across the film grows as iδ and draws chloride in by migration faster than its neutral oxidized form can diffuse out, so the oxidant concentration that the kinetic plateau implies at the electrode is " + accum(thA).toFixed(1) + " times the bulk chloride there against " + accum(thM).toFixed(1) + " on the microfluidic film. These currents rest on the chloride's diffusivity in its 6:1 acetonitrile/aqueous HCl medium, which is declared: across the bracket of Table S7d the row's ceilings move \u00d7" + MXF.cases.cl34_lo.ratio_lo.toFixed(2) + "\u2013\u00d7" + MXF.cases.cl34_hi.ratio_hi.toFixed(2) + " and every cell stays above " + Math.floor(Math.min(MXF.cases.cl34_lo.lowest_cell_mAcm2, MXF.cases.cl34_hi.lowest_cell_mAcm2)) + " mA cm\u207b\u00b2, so the shape described here holds while its magnitudes do not. That maximum is a property of a 14 mM carrier in 85 mM supporting salt as the model treats it, with one lumped neutral oxidant, and is not claimed beyond it. The amidyl-radical amination runs with sodium bromide as mediator and sole electrolyte, so the carrier reaches the anode by migration as well as diffusion. At the Hofmann entry's constant its reaction layer (x_k = " + amU.xk.toFixed(0) + " μm) is thinner than the film only in the two batch cells: there " + fRange(AMDB.map(c => 100 * AMDC(c)), v => v.toFixed(0)) + " % of the substrate remains at the wall and the ceiling stands " + fRange(AMDB.map(ecAmp), v => v.toFixed(1)) + " times above the bromide's diffusive bound, and in every other film the row sits at " + fRange(AMDO.map(c => c.ec / npK0(c.rxn, c.reactor)), v => v.toFixed(2)) + " times the bromide's migration-limited ceiling.";
  })()),
  p("The same content can be read nondimensionally, and doing so removes the solvent and carrier properties from the comparison entirely. Against the reactor intensification x̂, the three carrier laws that follow from Eqs. S1 and S12–S15:"),
  eqn([{m:[mr("x̂"), mr("="), mfr([msub("δ","batch")], [mr("δ")])]}, {t:";   "}, {m:[msub("ŷ","direct"), mr("="), mr("x̂")]}, {t:";   "}, {m:[msub("ŷ","catalyst"), mr("="), mr("ε"), mr("x̂")]}, {t:";   "}, {m:[msub("ŷ","mediated"), mr("="), mfun("min", mrb([mr("x̂"), mr(","), mfun("max", mrb([mr("μ"), mr("x̂"), mr(","), mr("μ"), msup("λ","1∕2")]))]))]}], "S17"),
  p("with μ = n_c C_med D_med/(n_S C_S D_S), ε = n_c C_cat D_cat/(n C_S D_S), and λ^½ = δ_batch/x_k the batch Damköhler group; the min enforces the substrate cap (Eq. S15) and the max the commuting floor (Eq. S13). The electron stoichiometries are not optional in μ: for the ACT exemplar that fixes its value (n_c = 1 per mediator turnover, n_S = 4 per substrate, the alcohol going to the acid; C_med = 25 mM, C_S = 0.50 M, D_med = 5.93 × 10⁻¹⁰ and D_S = 7.22 × 10⁻¹⁰ m² s⁻¹) the ratio is 0.0103, and dropping n_S quadruples it to 0.041."),

  h2("S5.6 Verification against analytic limits"),
  p("Every continuum-model configuration with a tractable analytic limiting current was compared against the solver. All sixteen checks pass. Stage-1: the Fick limit nFDC/δ for a neutral reactant in 10× supporting electrolyte is reproduced to +0.00%; the Newman binary-electrolyte migration factor of exactly 2 for an anion oxidized in its own salt to +0.50%; the linear-profile prediction c_surf/c_bulk = ½ at i = ½·i_lim to +0.63%; and mesh refinement from N = 40 to 160 moves the Fick comparison by ≤1%. Stage-2: the k→0 commuting bound F·D_red·C_med/δ is reproduced to " + AG_COMMUTE + "% (mesh-independent to 0.1% between N = 90 and 130); the Newman factor of 2 through the EC′ code path to +0.26%; and the Savéant plateau at δ/x_k = 7.9 to " + AG_SAV + "% — after applying the first-order substrate-depletion correction i = i_sav·(1 − A/γ)^½; without it the asymptote overestimates by A/2γ (here 10%), which accounts for the raw deviation. Total catalysis at k = 10³ M⁻¹s⁻¹ is an asymptote rather than an equality, so the comparison is a bracket: the solver plateau must lie within [0.80·i_cap, i_cap + i_shuttle] and must never exceed the ceiling; it sits at 0.87·i_cap, approached monotonically from below."),
  p("These comparisons surface one genuine numerical limitation — on a hyper-stretched geometric mesh (fixed 0.03 μm first cell) the damped-Newton continuation stalled before full surface depletion in the deep-depletion migration regime of concentrated ionic mediators (1.43× the Fick bound where the analytic answer is 2.00×) — and four features of the solver address it: (i) the residual scaling floor for trace species is tied to the dominant concentration instead of the trace bulk, which removes the ill-conditioning (the same binary comparison on the stretched mesh converges to within 0.2% of the ceiling); (ii) the first mesh cell is matched to the reaction layer, dx1 ≈ x_k/50 bounded by the uniform spacing; (iii) the reported i_lim is obtained by concentration control, which reaches a surface plateau rather than approaching it through the ramp's fold; (iv) the homogeneous stoichiometries are explicitly charge-conserving (Σ z·ν = 0, with proton/hydroxide partners as species), enforced by runtime assertions together with Σ z·s = 1 and bulk electroneutrality. The discrete statement a referee would test is then verified — the ionic current F·Σ z_j·N_j evaluated at every interior face equals the applied current — and passes at machine precision (max deviation 3×10⁻¹²). The production mediated matrix (Table S6) is solved with these constraints in force; its chloride/ethylene entry sits at " + fRange(EC.filter(c => c.rxn === ETH).map(c => c.ec / c.t0), v => v.toFixed(2) + "×") + " its Fick bound across the architectures, on the analytic migration ceiling, and the propylene ex-cell solve of §S4 returns " + EX.reachable_ratio_to_fick.toFixed(3) + "×."),

  h2("S5.7 Catalyst-carried entries"),
  p("Mechanistically a molecular catalyst is an EC′ carrier like a mediator: the electrode generates the active oxidation state and the substrate consumes it in solution, at a rate k c_active c_S, and the ceiling is the EC′ solution of §S5.4 with the same species set as the k = 0 layer plus the substrate at its reported concentration and a charge-balancing product of the homogeneous step. Credited with no turnover inside the film (k = 0) the catalyst is a shuttle — activated at the electrode, carried out through the film unreacted — and its ceiling is n_c F D_cat C_cat/δ, the carrier's own transport bound, which is the floor of the EC′ current because the homogeneous source can only add flux. That treatment is a direct electrolysis of a dilute species and can show nothing catalytic. The mediated rows each carry a rate constant for a single step (Table S6); the catalyst rows are multi-step cycles, and the constant the model needs is that of the first step that consumes the substrate."),
  p("For " + numWord(SR.n_sourced) + " of the " + numWord(N_CAT) + " rows that step has been measured (nickel) or estimated by simulating cyclic voltammograms (cobalt hydride) on a related system, and that value is adopted as a declared transfer to the row's own ligand, solvent and substrate (state C, Table S7j). Two nickel rows, the kilogram-scale cross-electrophile coupling and the biaryl homocoupling, turn over by oxidative addition of an aryl bromide to a low-valent nickel bipyridine. For the isolated Ni(I) complex [(CO₂Et-bpy)NiCl]₄ in THF at 26 °C that step is 7.1 ± 0.3 M⁻¹ s⁻¹ with bromobenzene and 3.4–56 M⁻¹ s⁻¹ across the para-substituted series (Hammett ρ = +1.1), and the zerovalent phosphine complex Ni(0)(PEt₃)₄ reacts with bromobenzene at 2.9 M⁻¹ s⁻¹, a value Ting et al. quote from Tsou and Kochi;«ting2022» the voltammetry behind the aryl-amination exemplar, in DMF, loses the Ni(II/I) return wave at 100 mV s⁻¹ on adding 4-bromoanisole, which places the step at or above ≈10² M⁻¹ s⁻¹ in a medium of this class (30 mM 4-bromoanisole; k ≳ (Fv/RT)/[ArBr] = 3.9 s⁻¹/0.030 M ≈ 1.3 × 10²);«kawamata2019» and pulse radiolysis of (dtbbpy)NiBr with 4-bromobenzotrifluoride bounds it below 10⁴ M⁻¹ s⁻¹.«till2021» The coupling solves a bromoindole that was not measured. The homocoupling solves bromobenzene; its exemplar adds the first aryl bromide to the zerovalent complex Ni(0)(bpy), generated at the cathode, and the second to the aryl–Ni(I) intermediate,«courtois1997» so for that row the measured constants are analogues in ligand for both additions and in oxidation state for the first. The adopted value is 10² M⁻¹ s⁻¹, between the constants on the model complexes and the upper limit on the row's own ligand, with 10¹–10⁴ as its sensitivity; both bromobenzene constants on the model complexes lie below that band" + niK1Sent() + ". Two cobalt-hydride rows (the alkene reduction, and the isomerization, a chain that passes 3 F mol⁻¹ for the compound it carries and is left out of the class medians, Table S10) turn over by the reaction of Co(III)–H with the alkene. A voltammetric simulation of the Co(salen) hydride with a styrene in DMF agrees qualitatively with the measured voltammograms at k_MHAT = 7 × 10² M⁻¹ s⁻¹, the authors stating that no full parametric fit was made, simulating the step as insertion of Co–H into the styrene followed by Co–alkyl homolysis, and noting that their results do not favor one mechanistic pathway over another, with hydride formation turnover-limiting in that study«boucher2023» and in the work of Wilson and Holland;«wilson2024» the exemplar's own kinetics, measured on its Co(salen) cycloisomerization, are first order in the alkene, and with bipyridine ligands, the class the reduction uses (studied under its conditions A), the exemplar suggests that migratory insertion may be more consistent than hydrogen-atom transfer, while for its Co(salen)-1 system, the catalyst of the isomerization row, it proposes hydrogen-atom transfer (p. 693); no kinetics are reported for the conditions of the reduction.«gnaim2022» The value 7 × 10² is adopted with 10¹–10⁴ as its sensitivity, reaching almost two decades below the measurement because both rows solve unactivated alkenes, for which the simulation's authors note that a distinct mechanism is possible. The remaining " + floorRowsWord() + " rows carry no measured constant for the step the model needs and stay at k = 0, the floor, with the declared band of k as their sensitivity. For three of them a finite constant would describe the wrong step. In the two nickel aminations the cycle is split between the electrodes: Ni(I) is made at the cathode and adds the aryl bromide, and the amine enters at Ni(II) and leaves after an anodic oxidation to Ni(III),«kawamata2019,liu2025» so no single electrode regenerates the carrier inside its own film. The Co(salen) allylic C–H amination regenerates no catalyst at room temperature, the exemplar's voltammetry showing the Co(III) cation binding the deprotonated carbamate without returning to Co(II), and turns over by a heat-induced homolysis, a first-order step that a bimolecular constant cannot represent (the synthesis runs at reflux).«cai2021» The other five are the Ni(tet a) macrocycle cyclization, the manganese diazidation (an azidyl-radical step), the copper/anthraquinone photoelectrochemical cyanation (the substrate is consumed by the photoexcited quinone), the rhodium C–H alkenylation and the nickel doubly decarboxylative coupling (its redox-active esters are reduced by a low-valent nickel species whose rate the exemplar does not report). The sourced cells are overlaid on the published matrix exactly as the mediated cells are (Table S5), and the k = 0 member of every solve reproduces the published cell to " + (SR && Math.abs(SR.control.worst_rel) < 1e-4 ? "better than 0.01" : (SR ? (100 * Math.abs(SR.control.worst_rel)).toFixed(2) : "?")) + " % — the control that the sourced layer is the same problem with the source switched on."),
  p((function () {
    // chemistry audit, 2026-10-05 (night): the third row of Fig. 6h is the Ni aryl-aryl homocoupling at the nickel constant;
    // the Co(salen) allylic C-H amination, which has no measured constant, left the panel (combined_figure.py _HROWS)
    var rows = [["Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "Ni–XEC"], ["Co-H alkene reduction (e-HAT)", "cobalt hydride"],
                ["Cathodic Ni aryl-aryl homocoupling", "Ni homocoupling"]];
    var g = rows.map(function (r) { var q = srRow(r[0]); if (!q) throw new Error("S5.7: no sourced row " + r[0]); return "×" + q.gain_unstirred_to_rce.toFixed(1) + " (" + r[1] + ")"; });
    var g0 = rows.map(function (r) { return "×" + srRow(r[0]).gain_at_k0.toFixed(0); });
    var and3 = function (xs) { return xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1]; };
    return "The three rows drawn in main-text Fig. 6h gain " + and3(g)
      + " from the unstirred to the rotating-cylinder film at their cited rate constants, against " + and3(g0)
      + " for the same rows at k = 0. A transport-limited carrier gains the full 1/δ ratio; a carrier regenerated inside its own reaction layer gains only a few-fold.";
  })()),
  p("Sensitivity. All " + numWord(N_CAT) + " rows are also re-solved over a declared band k ∈ {" + ckK.map(k => ckSci(k)).join(", ") + "} M⁻¹ s⁻¹, which brackets every adopted value and supplies the floor rows' sensitivity. The substrate diffusivity is the second input: the Wilke–Chang estimate of Eq. S2 for the substrate each exemplar names, in the row's own solvent (listed in the table below; Table S7d). It enters only through the substrate cap n_S F D_S C_S/δ, and the table marks the rows whose ceiling sits at that cap. The k = 0 member of every sweep reproduces the published k = 0 cell to " + (Math.abs(CK.control.worst_rel) < 1e-4 ? "better than 0.01" : (100 * Math.abs(CK.control.worst_rel)).toFixed(2)) + " % (worst of " + CK.control.cells + " cells)."),
  p("Result. " + ckSentence().replace(" (§S5.7)", "") + " " + srCountMoves() + " " + ckBandSentence() + (ckAt(ckKmax).rows_clearing25.length ? " The rows that clear 25 mA cm⁻² somewhere within the band: " + ckClearList() + "." : "") + " " + ckWalls() + " The design consequence for the main text follows directly: a catalyst-carried row with a fast homogeneous step behaves as a direct electrolysis of a dilute substrate, and its levers are the substrate concentration and the architecture; one with a slow step is capped by the catalyst loading; and in the kinetic regime between them, where the " + numWord(SR.n_sourced) + " sourced rows sit, thinning the film buys a few-fold rather than the 1/δ of a transport-limited row."),
  mkTable(["Catalyst-carried entry", "C_cat (mM)", "C_S (M)", "substrate (D_S, 10⁻⁹ m² s⁻¹)", "k adopted (M⁻¹ s⁻¹)", "published ceiling, best of seven (mA cm⁻²)", "best at k = 0", "best at k = " + ckSci(ckKmax), "max × in band", "at substrate cap"],
    ckRows.map(([nm, r]) => { const q = srRow(nm); return [ckShort(nm), r.C_cat_M != null ? (1000 * r.C_cat_M).toFixed(1) : "", r.C_S_M != null ? r.C_S_M.toFixed(3) : "",
      catSub(nm),
      q ? srK(q.k_M) : "0 (floor)", q ? q.best_mAcm2.toFixed(2) : r.i_k0_best_mAcm2.toFixed(2),
      r.i_k0_best_mAcm2.toFixed(2), r.i_ec_best_mAcm2_at_kmax.toFixed(1), r.max_amplification.toFixed(1),
      (q ? q.cells_at_substrate_cap > 0 : r.substrate_capped_at_kmax) ? "yes" : "no"]; }),
    [2.6, 0.8, 0.8, 2.3, 1.1, 1.4, 0.9, 0.9, 0.8, 0.9]),
  cap("The " + numWord(N_CAT) + " catalyst-carried rows: the substrate each exemplar names with its Wilke–Chang diffusivity in the row's solvent, the adopted rate constant (§S5.7, Table S7j), the ceiling the matrix publishes at it (the largest of the seven architectures), and the declared-band sweep around it. A row is at its substrate cap when a published cell (or, for a floor row, its ceiling at k = " + ckSci(ckKmax) + ") is within 5 % of n_S F D_S C_S/δ; there D_S is what sets the number."),
  p("Table S11 lists, for each of the " + numWord(KBR.length) + " rows solved with the homogeneous source term (the " + numWord(KBR.filter(r => r[kbc("carrier_class")] === "mediator").length) + " mediated rows and the " + numWord(KBR.filter(r => r[kbc("carrier_class")] === "catalyst").length) + " catalyst-carried rows carried at a rate constant), the homogeneous step the row solves, the system the constant was measured on and the value its source prints. " + kbRelationSentence() + " The last column gives the row's best ceiling of the seven architectures at the adopted constant, and its range when the constant is moved by a factor of ten either way (mediated rows, the sweep of §S5.5) or across its bracket (catalyst rows, above). The two cobalt-hydride rows share one constant; the isomerization runs as a chain and is left out of the class medians (Table S10)."),
  mkTable(["Entry", "Step solved", "k (M⁻¹ s⁻¹)", "Measured on", "Value in the source (M⁻¹ s⁻¹)", "Relation", "Best ceiling at k (range), mA cm⁻²"],
    kbTableRows(), [1.9, 2.5, 0.8, 3.6, 2.3, 1.5, 1.5]),
  cap("Table S11. The rate constant of each mediated row and of each catalyst-carried row that has one: the homogeneous step the row solves, the system on which the constant was measured, the value the source prints for it, how the measured system relates to the row's, and the row's best ceiling of the seven architectures at the adopted constant with its range over a tenfold change of the constant either way (mediated rows) or over the bracket of §S5.7 (catalyst rows). A turnover frequency is printed as the source gives it. The " + numWord(SR.n_floor) + " catalyst-carried rows with no measured constant are solved at k = 0 and are not listed."),
  h1("S6. Cell voltage and the Joule-heating ceiling"),
  p("The cell-voltage stack is"),
  eqn([{m:[msub("E","cell"), mrb([mr("i")]), mr("="), msub("E","0"), mr("+"), mr("2"), mfr([mr("2RT")], [mr("F")]), mfun("asinh", mrb([mfr([mr("i")], [mr("2"), msub("i","0")])])), mr("+"), mfr([mr("i"), mr("L")], [mr("κ")])]}], "S18"),
  p("with a representative E₀ = 2.0 V thermodynamic-plus-kinetic floor and symmetric Butler–Volmer asinh terms for the two electrodes (α = ½, i₀ = 1 mA cm⁻² per electrode; both illustrative — " + ASH_SENT + "). The Joule dissipation per electrode area is"),
  eqn([{m:[mr("Q"), mr("="), mfr([msup("i","2"), mr("L")], [mr("κ")])]}], "S19"),
  p("At 100 mA cm⁻² across the canonical 2 cm beaker gap of §S6.1, in 0.2 M NaI/DMF (κ = " + NAI.k + " mS cm⁻¹, the registered preparative electrolyte adopted for §S6), E_cell = " + DMFX.E_cell_V.toFixed(1) + " V, of which " + DMFX.ohmic_V.toFixed(1) + " V is ohmic; the same cell at 50 mA cm⁻² draws " + DMFX.E_cell_50_V.toFixed(1) + " V. The overpotential heat at 100 mA cm⁻² is q = " + DMFX.q_Wcm2.toFixed(1) + " W cm⁻². A 100 mL batch of DMF under 10 cm² of such electrode (m·c_p = 194 J K⁻¹) initially self-heats at ≈" + (DMFX.q_Wcm2 * 10 / 194 * 60).toFixed(1) + " K min⁻¹, and the full lumped balance of §S6.1 places its passive steady state at T_ss ≈ " + DMFX.T_ss_C.toFixed(0) + " °C, above DMF's 153 °C boiling point. Both of those statements are conditional on the adopted κ and must be quoted with the condition, because that κ is derived rather than measured (§S9, Table S7f): Λ° = 81.35 is measured directly, and the attenuation at 0.2 M is transferred from a measurement of the same salt in methanol, which makes " + NAI.k + " likely to err low rather than a best estimate, a direction and not a bound (Table S4). T_ss falls back to the boiling point at κ = " + DMFX.kappa_Tss_at_boil_mScm.toFixed(2) + " mS cm⁻¹, a margin of " + xmul(DMF_TSS_FOLD, 2) + ", and the " + DMFX.E_cell_50_V.toFixed(1) + " V figure leaves the 10–20 V band at κ = " + DMFX.kappa_E50_10V_mScm.toFixed(2) + " mS cm⁻¹ (×" + (DMFX.kappa_E50_10V_mScm / Number(NAI.k)).toFixed(2) + ") or κ = " + DMFX.kappa_E50_20V_mScm.toFixed(2) + " mS cm⁻¹ (×" + (DMFX.kappa_E50_20V_mScm / Number(NAI.k)).toFixed(2) + "). Both thresholds lie inside the 4–16 mS cm⁻¹ band of that row, so both statements are conditional on the adopted κ. What the worked example supports without that qualification is the direction: at any κ in the band the cell dissipates ohmically far more than it dissipates kinetically, and the conclusion is not that it runs hot but that it approaches boiling. At the adopted κ, 100 mA cm⁻² is not passively reachable in an unstirred beaker of DMF, consistent with the " + T_CEIL("DMF", T_ARCH[0]).toFixed(0) + " mA cm⁻² passive ceiling §S6.1 reports for the same electrolyte and gap; the same experiment in 3.0 M LiBr/THF crosses THF's 66 °C boiling point in under two minutes. The same example in 0.1 M Bu₄NBF₄/DMF — measured at κ = 4.76 mS cm⁻¹ (Table S7f) — across a 5 mm gap gives " + f2(EX_ECELL) + " V, of which " + f2(EX_OHMIC) + " V is ohmic, " + f2(EX_Q) + " W cm⁻² of heat and a passive steady state of " + EX_TSS.toFixed(0) + " °C. That is the illustration the main text carries, and it is a tighter cell than the canonical beaker archetype rather than one of the modelled architectures: at the 2 cm spacing of §S6.1, on the registered preparative electrolyte, the conclusion inverts. The remedy is geometric and architectural, not chemical: the same electrolyte in the 25 μm gap of the microfluidic archetype carries " + CF.dmf_ohmic_ratio_2cm_over_25um.toFixed(0) + " times less ohmic heat at equal current — a " + CF.dmf_heat_ratio_2cm_over_25um["50"].toFixed(0) + "-fold reduction in the total heat load at 50 mA cm⁻² and " + CF.dmf_heat_ratio_2cm_over_25um["100"].toFixed(0) + "-fold at 100 mA cm⁻² once the activation term is included — and the cooled bipolar-plate architectures of PEM electrolyzer stacks reject 0.32–0.42 W cm⁻² into the anodic fluid at 2 A cm⁻², with in-cell gradients of 13.6–17.1 K (Eichner et al., Front. Chem. Eng. 2024, 6, 1384772, pp. 12 and 14). A thermodynamic check gives the same order: a PEM electrolyzer at 2 A cm⁻² and 1.9 V against a 1.48 V thermoneutral voltage generates 0.84 W cm⁻², and at 3 A cm⁻² and 2.1 V, 1.9 W cm⁻². Liquid cooling is not taken from that literature at all but built for each architecture as it would be cooled, a water jacket over the glass wall of a vessel cell and a cooled graphite plate behind the electrode of a thin cell, with the cell's own electrolyte-side film and a laminar water channel heated from one wall in series (Incropera Table 8.1, Nu = 5.39), which gives U′ = " + CF_LIQTXT("RDE 1600 rpm") + " W cm⁻² K⁻¹ for the vessel cells with forced electrolyte flow and " + CF_LIQTXT("zero-gap PEM stack") + " W cm⁻² K⁻¹ for the stack (Table S7i). Passive rejection is far weaker and is bounded by geometry rather than by any assumed cooling envelope: the construction of §S6.1 gives U′ = " + U_UNST.toFixed(4) + " W cm⁻² K⁻¹ for a 100 mL beaker in still air, rising only to " + U_STIR.toFixed(4) + " W cm⁻² K⁻¹ when the liquid is stirred. It is this coefficient, not any transport figure of merit, that bounds the current density a beaker-scale non-aqueous cell can sustain thermally."),
  h2("S6.1 Steady-state temperature and boil-off current"),
  p("To answer whether cells actually reach solvent boil-off rather than merely dissipating uncomfortable power, we close a lumped energy balance on a representative 100 mL cell with 10 cm² electrodes. The dissipated overpotential heat per electrode area, the steady state, the boil-off current, and the exact transient are"),
  eqn([{m:[mr("q"), mrb([mr("i")]), mr("="), msb([mr("2"), mfr([mr("2RT")], [mr("F")]), mfun("asinh", mrb([mfr([mr("i")], [mr("2"), msub("i","0")])])), mr("+"), mfr([mr("i"), mr("L")], [mr("κ")])]), mr("·"), mr("i")]}], "S20"),
  eqn([{m:[msub("T","ss"), mr("="), msub("T","amb"), mr("+"), mfr([mr("q"), mrb([mr("i")])], [mr("U′")])]}, {t:";     "}, {m:[mr("q"), mrb([msub("i","boil")]), mr("="), mr("U′"), mrb([msub("T","b"), mr("−"), msub("T","amb")])]}], "S21"),
  eqn([{m:[mr("T"), mrb([mr("t")]), mr("="), msub("T","amb"), mr("+"), mfr([mr("P")], [mr("UA")]), mrb([mr("1"), mr("−"), msup("e","−tUA∕C")])]}, {t:",   "}, {m:[msub("t","boil"), mr("="), mfr([mr("C")], [mr("UA")]), mfun("ln", msb([mfr([mr("P")], [mr("P"), mr("−"), mr("UA"), mr("Δ"), msub("T","b")])]))]}, {t:"   (exists only if P > UA ΔT_b)"}], "S22"),
  p("where U′ = UA/A_elec is the heat-rejection coefficient referred to electrode area, P = q·A_elec, and C = m·c_p the electrolyte heat capacity. The passive coefficient is derived from the reactor geometry. Treating the internal and external films in series and referring the result to electrode area gives U′ = [(1/h_int + 1/h_ext)⁻¹]·σ, with σ = A_external/A_electrode the ratio of heat-rejecting surface to electrode area, h_ext = " + THERM.h_ext_Wm2K.toFixed(1) + " W m⁻² K⁻¹ for natural convection plus radiation at 65 °C (radiation is comparable to convection at 60–150 °C and omitting it would overstate the boiling problem), and h_int ≈ 100, 800 and >2000 W m⁻² K⁻¹ for stagnant, stirred and forced-flow electrolyte respectively. For the 100 mL beaker, σ is the wetted wall plus base of a 100 mL charge in a 5 cm inside-diameter vessel (fill height 5.09 cm): A_external = 0.00996 m² over 10 cm² = 1×10⁻³ m² of electrode, so σ = " + SIG_B.toFixed(2) + " and U′ = " + U_UNST.toFixed(4) + " W cm⁻² K⁻¹. This is " + _pct(1 - U_UNST / TSUP.assumed_U) + " below 0.02 W cm⁻² K⁻¹, the upper edge of the natural-convection band drawn in main-text Figure 7(d), and using it lowers every passively cooled beaker ceiling by " + ASSUMED_DROP + " relative to that edge. h_ext is held at its 65 °C value; at DMF's boiling point the coefficient rises to " + TSUP.h_ext_hot_Wm2K.toFixed(1) + " W m⁻² K⁻¹, which would raise the DMF beaker ceiling by " + HEXT_RISE + ". The same construction exposes a consequence that a fixed cooling axis conceals: intensified cells are compact, so their σ falls (≈7 for the microfluidic chip, ≈0.8 for an interior cell of a zero-gap stack, which is enclosed by its neighbours), while the three archetypes that intensify transport without changing the cell body — the recirculating flow cell and the two rotating electrodes — inherit the beaker's σ = " + SIG_B.toFixed(2) + " because none of their exemplars states an electrode area. Neither declared value has a source; each is reproduced by a package geometry given in Table S7i, and the σ those three take from the beaker is swept there as a breaking point rather than as a band. Intensification therefore carries a heat-rejection penalty that partly offsets its heat-generation advantage, and stirring a beaker is nearly useless thermally (U′ rises only " + U_UNST.toFixed(4) + " → " + U_STIR.toFixed(4) + " W cm⁻² K⁻¹) because h_ext, not h_int, is the limiting resistance. Active thermal management is treated as a separate axis in §S6.2 rather than bundled into a geometry label."),
  p("One consequence of that series structure deserves stating explicitly, because the lumped "
     + "h_int is least defensible exactly where a reader is most likely to challenge it. At the "
     + "25 \u00b5m gap of the microfluidic archetype the thermal entry length is a substantial "
     + "fraction of the channel and "
     + "axial conduction is not obviously negligible, so a fully developed Nusselt number is not "
     + "the right basis for h_int there. Both objections are correct as physics and neither can "
     + "reach a published number, because both are corrections to h_int and h_int is the larger "
     + "of two series conductances by a factor of "
     + Math.round(HB.reactors["microfluidic 25 $\\mu$m"].h_int_over_hext) + ". Replacing it with "
     + "a perfect internal film \u2014 h_int \u2192 \u221e, which bounds every developing-flow "
     + "or entry-length correction that could ever be made \u2014 raises U\u2032 on that row by "
     + (100 * HB.reactors["microfluidic 25 $\\mu$m"].rel_change_up).toFixed(2) + "%. The "
     + "quantity that would have to be re-derived to answer the objection properly is therefore "
     + "one that cannot move a ceiling, a margin or a verdict."),
  p("Electrolyte selection for the thermal analysis of §S6 is constrained to entries that carry provenance in the registry of Table S7f, and prefers preparative compositions whose concentration is page-anchored to a named process. Two of the four conductivities are measured — MeCN and the aqueous reference — one is derived (DMF) and one remains an assumption (THF), and each is quoted below with the margin at which the statement it supports would flip. THF uses 3.0 M LiBr/THF, whose composition is page-anchored to the scale-up Birch reductions of Peters et al.«peters2019» (83.4 g LiBr in 320 mL THF for the 10 g batch run, SM p. S15; the 100 g flow run uses the same 3.0 M stock, 7.5 mol in 2.5 L, SM p. S21) but whose conductivity, κ ≈ 3 mS cm⁻¹, is an order-of-magnitude estimate for a heavily ion-paired ether medium and not a measurement — THF has ε = 7.6 and a Bjerrum critical distance of 3.7 nm, so association is essentially complete and no limiting-conductivity route can reach it. No one margin applies to every §S6.1 verdict for this row; the reversals of the passing verdicts are quoted first, then the nearest reversal of a failing verdict, which is the binding one. Recomputed from the lumped thermal model at κ = 3.0 mS cm⁻¹ and T_b = 66 °C, and judged against each architecture's own transport ceiling, THF does not boil in the batch cells, the recirculating cell or the microfluidic chip: those verdicts would reverse only at " + THF_PASS_LO.toFixed(2) + "–" + THF_PASS_HI.toFixed(2) + "× the carried conductivity, below it in every case and, for the unstirred, stirred and recirculating cells, inside the band. Where THF does fall short the multipliers are " + xmul(THF_BIND[1].multiple) + " (" + ARCH_SHORT(THF_BIND[0]) + ") and " + xmul(THF_RCE) + " (rotating cylinder), and the zero-gap stack is unreachable on κ at all, its activation term alone putting out 0.71 W cm⁻² at 1000 mA cm⁻² against " + (THERM.reactors.find(r => /stack/.test(r.name)).U_passive * (66.0 - THERM.T_amb_C)).toFixed(3) + " W cm⁻² of passive rejection. The binding verdict is the " + ARCH_SHORT(THF_BIND[0]) + " at " + xmul(THF_BIND[1].multiple) + ", against a band whose top is " + xmul(CF_V("THF", "RDE 1600 rpm").band_multiple[1], 2) + " the carried value. The THF liquid-cooling verdicts of §S6.2 are tighter still: they leave the declared cooler range below " + CF_THF_LIQ_TXT() + " the carried conductivity, inside the band, and §S6.2 states them conditionally. The hard floor for this row is the state-B 0.206 mS cm⁻¹ obtained from the cell resistance of Lee et al., Org. Process Res. Dev. 2022, 26, 2674–2684. Das's measurement at the highest concentration in the sources retrieved here, κ = 0.256 mS cm⁻¹ at 0.316 M (J. Solution Chem. 2008, 37, 947–955, Table 1), would bound κ(3.0 M) from below only if 3.0 M sat below the conductivity maximum, which the solvation count below argues it does not. Across the band the boil-off verdicts of the microfluidic chip, the rotating cells and the stack do not turn: the chip clears at every point in it and both rotating cells and the stack fail at every point in it. What the band alone decides among the boil-off verdicts is the unstirred, stirred and recirculating cells, which clear at the carried value and above and boil before reaching their own transport ceilings only below " + listAnd(CF_THF_CM.map(v => (v.flip_down_multiple * parseFloat(ELEC.get("3.0 M LiBr/THF").kappa)).toFixed(2))) + " mS cm⁻¹ respectively, inside the band and above its state-B floor of 0.206 mS cm⁻¹. Das's twenty points rise as κ ∝ c^n over the top decade of the measured range (n = 1.75–2.20 depending on the fitting window); continued to 3.0 M they give 10.9–35.6 mS cm⁻¹, all below the rotating-disc reversal at " + THF_BIND[1].kappa_reverse_mScm.toFixed(1) + " mS cm⁻¹. None of those continuations is physically sound. Peters' own recipe is 83.4 g LiBr (" + PET.libr.toFixed(3) + " mol) in 320 mL THF (" + PET.thf.toFixed(2) + " mol), which is **" + PET.ratio.toFixed(2) + " mol THF per mole of salt**; since Li⁺ in an ether is four-coordinate, the cation's solvation shell alone takes " + PET.bound4 + "% of it, leaving almost nothing for Br⁻ or for bulk solvent — and the conclusion survives across the plausible range of coordination number, since even at n = 3 only " + PET.free3 + "% of the THF is free. Das's highest measured point, by contrast, has 39 mol THF per mole of salt. The two concentrations are not the same kind of liquid: the c^1.75 branch describes ions migrating through bulk THF, and at 3.0 M that bulk does not exist, so κ must already have passed its maximum. Cai et al. (J. Am. Chem. Soc. 2023, 145, 25716–25725), running 2 M LiBF₄ in THF, report from molecular dynamics that Li⁺ in cyclic ethers is only partially solvated and the ions form contact ion pairs and aggregates — the same solvation-starved picture. This fixes the direction but does not locate the maximum, so no upper bound on κ is established. The aqueous reference uses 1 M NaOH (κ = 174.5 mS cm⁻¹, interpolated between two measured points of the Dorn isotherm), and the CRC route corroborates it: the applicable table is not p. 5-74, the 25 °C equivalent-conductivity table that stops at 0.1 M, but p. 5-71 (\"Electrical Conductivity of Aqueous Solutions\", 20 °C, 0.5–50 mass %) reaches this row directly and, combined with the concentrative-properties conversion 1.000 M = 3.840 mass % and a 20 → 25 °C correction at α = 1.5–1.9%/K, derives 174–182 mS cm⁻¹.«crc» The adopted 174.5 mS cm⁻¹ is not that derivation but a measurement, read off a raw isotherm rather than reconstructed; it sits at the lower edge of the CRC-derived band, which corroborates it. The aqueous margins are " + NAOH_RANGE + " across the preparative architectures and survive anywhere in the band, and its nearest conductivity reversal needs a " + xmul(1 / NAOH_NEAR.flip_down_multiple) + " fall. MeCN uses 0.25 M Bu₄NBF₄ (κ = 19.95 mS cm⁻¹), measured: it is read directly off the raw isotherm in the Supporting Information of Dorn et al., J. Chem. Eng. Data 2024, 69, 1493–1502, rather than reconstructed by Casteel–Amis from the fit the article body prints in Table 3, p. 1499. That reconstruction gives " + CA_KAPPA.toFixed(2) + " mS cm⁻¹, " + CA_PCT + "% from the measured value. The value is cross-checked at 1 M against Gong et al., Energy Environ. Sci. 2015, 8, 3515–3530, whose tabulated value the same fit reproduces to within 2%; the band is 15–23 mS cm⁻¹. Its failing verdicts at the rotating disc and the rotating cylinder reverse only at " + xmul(CF_V("MeCN", "RDE 1600 rpm").flip_up_multiple, 2) + " and " + xmul(CF_V("MeCN", "rotating cyl. 3000 rpm").flip_up_multiple, 2) + " the carried value, outside that band, and the zero-gap stack's is unreachable on κ." + (THERM.si_support.kappa_flips.MeCN["zero-gap PEM stack"].kappa_reverse_mScm === null && THERM.si_support.kappa_flips.MeCN["zero-gap PEM stack"].passes === false ? "" : (() => { throw new Error("S6.1: the MeCN stack verdict now reverses on kappa"); })()) + (CF_V("MeCN", "RDE 1600 rpm").flip_up_multiple > CF_V("MeCN", "RDE 1600 rpm").band_multiple[1] ? "" : (() => { throw new Error("S6.1: a MeCN rotating-cell verdict now reverses inside its band"); })()) + " A mass-action bound of 24–36 mS cm⁻¹ is not used — it is a Lee–Wheaton extrapolation some 25× above its own fitted range, and a measured isotherm outranks an extrapolated bound. DMF uses 0.2 M NaI (κ = " + NAI.k + " mS cm⁻¹), which is derived rather than measured and is the most exposed number in the registry: its binding verdict (the " + ARCH_SHORT(DMF_BIND[0]) + ") reverses at " + xmul(DMF_BIND[1].multiple, 2) + "" + (DMF_BIND_IN_BAND ? ", inside the row's own 4–16 mS cm⁻¹ band," : "") + " and the steady-state sentence of §S6 resting on it flips at " + xmul(DMF_TSS_FOLD, 2) + ". λ°(Na⁺) = 29.81 and λ°(I⁻) = 52.11 S cm² mol⁻¹ in DMF at 25 °C are page-anchored to Gopal and Jha, Indian J. Chem. 1977, 15A, 80–83, Table 2, p. 81. Kohlrausch additivity of those two gives Λ° = 81.92 S cm² mol⁻¹, within 0.7% of the value Krumgalz and Barthel measure directly, Λ° = 81.35 ± 0.03 S cm² mol⁻¹ (Z. Phys. Chem. 1984, 142, 167–178, Table 2, p. 170), which is the value adopted and sets a hard ceiling κ ≤ cΛ° = 16.27 mS cm⁻¹. Λ(c) at the working 0.2 M has never been measured for this salt in this solvent, so the row is derived rather than measured: the attenuation is taken from Dorn's measured NaI-in-methanol isotherm at the same molarity (Λ/Λ° = " + NAI.r + ", read at molality " + NAI.m + " mol kg⁻¹) and applied to Λ° = 81.35 measured directly by Krumgalz and Barthel, giving " + NAI.k + " mS cm⁻¹. That transfer is expected to err low, which fixes the direction of its error but not a bound on it. §S6 uses preparative compositions rather than voltammetry-grade supporting electrolytes such as 0.1 M Bu₄NPF₆/THF (0.51 mS cm⁻¹ at 22.0 ± 1.0 °C; Zhang et al., JACS Au 2023, 3, 2280–2290, Table 1). That choice is not merely unrepresentative but self-invalidating: at its apparent " + CF.thf_pf6_example.i_boil_mAcm2.toFixed(1) + " mA cm⁻² ceiling the 2 cm cell requires " + CF.thf_pf6_example.E_cell_V.toFixed(1) + " V, of which " + CF.thf_pf6_example.ohmic_V.toFixed(1) + " V is ohmic, so the thermal limit sits far behind a voltage limit no laboratory supply would reach. Quoting a thermal ceiling that cannot be approached without an implausible cell voltage overstates the thermal problem while understating the ohmic one. With the preparative electrolytes adopted here the two constraints converge, which is the physically meaningful statement: both are expressions of the same iL/κ term."),
  p("This section separates the variables that decide whether a cell boils, across the preparative architectures of the transport ladder of Table S5 plus the zero-gap stack as an industrial reference; the ANEC cell, an analytical screening cell with a 0.32 cm² electrode (Jones et al., Rev. Sci. Instrum. 2018, 89, 124102), is left out, as it is from main-text Figure 7. Each preparative architecture is judged against its own median limiting current from the 50-reaction matrix (the zero-gap stack, an industrial reference, at its declared 1 A cm⁻²) rather than against a declared design current, so the analysis asks one question: at the current transport allows, can the cell reject the heat? Fixing the reactor — an unstirred beaker at the canonical 2 cm spacing, 10 cm² electrodes, passive cooling — and varying only the solvent: THF (3.0 M LiBr) boils at " + T_CEIL("THF", T_ARCH[0]).toFixed(0) + ", MeCN at " + T_CEIL("MeCN", T_ARCH[0]).toFixed(0) + ", DMF at " + T_CEIL("DMF", T_ARCH[0]).toFixed(0) + " and aqueous NaOH at " + T_CEIL("aq. NaOH", T_ARCH[0]).toFixed(0) + " mA cm⁻². Every ceiling in this section is a lower bound with respect to the temperature dependence of conductivity, because κ is evaluated at 25 °C while the cell approaches its boiling point; §S6.3 brackets that omission and the numbers here are its conservative end. The planar current distribution acts the other way for the beakers (§S6.2 (i)). Taking the same ceilings across the architectures against each one's own median transport ceiling, wherever the transport ceiling sits above a solvent's boil-off ceiling the cell boils before it reaches the current transport allows. Together these results show that in the batch and thick-gap flow cells nothing boils, because transport binds long before heat does — the unstirred beaker reaches only " + T_IDES[T_ARCH[0]].toFixed(1) + " mA cm⁻² on transport grounds, where even THF has a margin of " + f2(T_MARG("THF", T_ARCH[0])) + "×. Heat becomes the binding constraint only once transport is intensified. At the two rotating archetypes, whose transport ceilings are among the highest in the model at " + T_IDES["RDE 1600 rpm"].toFixed(0) + " and " + T_IDES["rotating cyl. 3000 rpm"].toFixed(0) + " mA cm⁻², all three organic solvents fall short under passive cooling (margins " + ORG_RANGE("RDE 1600 rpm") + "× at the disc and " + ORG_RANGE("rotating cyl. 3000 rpm") + "× at the cylinder), and only the aqueous reference clears. The THF failures there hold on every axis; " + listAnd(COND_ROT.map(p => T_PRETTY[p[1]] + " at the " + ARCH_SHORT(p[0]))) + " reverse inside the temperature bracket of §S6.3 or the surface-area sweep of §S6.4 (Table S12), and are conditional on where those inputs sit. In the unstirred, stirred and recirculating cells THF clears at its carried conductivity but would boil below about " + listAnd(CF_THF_CM.map(v => v.flip_down_multiple.toFixed(2) + "\u00d7")) + " of it respectively, inside its " + CF_BAND_TXT("THF") + " band, so those verdicts are conditional too." + (CF_THF_CM.every(v => v.U_req <= v.U_passive && v.conditional) ? "" : (() => { throw new Error("S6.1: a THF batch or recirculating verdict is no longer a conditional pass"); })()) + " The zero-gap stack fails in all four electrolytes, by factors of " + T_SOLV.map(x => f1(T_IDES["zero-gap PEM stack"] / T_CEIL(x, "zero-gap PEM stack")) + "\u00d7 (" + T_PRETTY[x] + ")").join(", ") + ". Across the whole ladder the absolute ceiling does not rise monotonically with intensification: for DMF it runs " + T_ARCH.map(a => T_CEIL("DMF", a).toFixed(0)).join(", ") + " mA cm\u207b\u00b2, flat wherever the gap is unchanged, rising only where it is thinned, and falling again in the stack, whose enclosed geometry withdraws more rejecting surface than its 100 \u03bcm gap saves in ohmic heat. The microfluidic cell clears all four, by " + f2(T_MARG("THF", "microfluidic 25 $\\mu$m")) + "× in THF, with a transport ceiling within a few per cent of the rotating disc's. This contrast identifies the key geometric distinction. Rotating an electrode thins the diffusion layer roughly twentyfold and moves no electrode, so it buys transport and no thermal headroom at all; only the microfluidic cell thins the GAP. That is the physical statement the section rests on: the boil-off ceiling is a balance between two terms that do not scale together \u2014 the ohmic heat a cell generates, which carries the gap and the conductivity, and the temperature rise its solvent allows before boiling \u2014 and the interelectrode gap sets the balance between these terms, because the gap is the only geometric term on the heat-generation side (σ sets the rejection side, §S6.4). At a centimetre gap the ohmic term carries " + CF_PCT(CF.ohmic_share_cm_gap[0]) + " to " + CF_PCT(CF.ohmic_share_cm_gap[1]) + " per cent of the heat at the boil-off ceilings and conductivity ranks the solvents; thin the gap and it collapses onto a kinetic floor that is the same for every solvent, leaving only the boiling point to rank them. §S6.2 turns that balance into a cooling duty. " + T_SHARED.length + " of the " + T_ARCH.length + " architectures in fact share the same 2 cm ohmic path (" + T_SHARED.join(", ") + "), so the lowest of their boil-off ceilings in each electrolyte sits within " + (Math.ceil(1000 * TGEO.ceiling_spread_on_shared_gap) / 10).toFixed(1) + "% of the highest while their transport ceilings span " + TGEO.transport_span_on_shared_gap.toFixed(1) + "×. Transport intensification and thermal intensification are different axes, and this is where that shows."),
  h2("S6.2 Cooling duty"),
  p("Where a cell does fall short the design question is not whether it boils but how much cooling it needs. Setting T_ss to the boiling point at the architecture's own transport ceiling inverts the balance for the required heat-rejection coefficient, U′_req = q(i_design)/(T_b − T_amb), compared against the liquid cooling each cell's own construction supplies and against what it rejects unaided. \"Passive\" here means no fan, no pump and no coolant loop: heat crosses the internal film and then an external film of h_ext = " + THERM.h_ext_Wm2K.toFixed(1) + " W m⁻² K⁻¹ (natural convection plus radiation) into still air, referred to electrode area through σ. That external film is the limiting resistance throughout, which is why stirring a beaker is nearly useless thermally and why what each cell supplies unaided is set almost entirely by its own σ: " + (() => { const u = THERM.reactors.filter(r => r.gap_m >= 0.01).map(r => r.U_passive); return Math.min(...u).toFixed(4) + "–" + Math.max(...u).toFixed(4); })() + " W cm⁻² K⁻¹ for the centimetre-gap cells at σ = " + T_SIGMA(T_ARCH[2]).toFixed(2) + ", " + T_U["microfluidic 25 $\\mu$m"].toFixed(4) + " for the microfluidic chip at σ = 7.0 and only " + T_U["zero-gap PEM stack"].toFixed(4) + " for an interior cell of a stack at σ = 0.8, which is enclosed by its neighbours. Where passive rejection falls short, " + listAnd(CF_NEED()) + ". " + CF_LIQ_SENT() + (CF_COND_ACTIVE.length ? " " + numWordCap(CF_COND_ACTIVE.length) + " of these verdicts move inside their electrolyte's conductivity band (" + listAnd([...new Set(CF_COND_ACTIVE.map(v => v.solvent))].map(x => x + " " + CF_BAND_TXT(x))) + ") — " + listAnd(CF_COND_ACTIVE.map(CF_FLIPTXT)) + " the carried value — so each is conditional on where the conductivity sits in its band; the other cooling verdicts of these cells hold across it." : "") + CF_AXES_SENT() + " At the carried conductivities nothing in the organic set demands cooling beyond classes that are ordinary engineering" + (CF_BEYOND.length ? "; in " + listAnd([...new Set(CF_BEYOND.map(v => v.solvent))]) + " that holds only above " + xmul(Math.max(...CF_BEYOND.map(v => v.flip_down_multiple)), 2) + " the carried value, inside the band, and only within the declared construction range with a coolant at " + THERM.T_amb_C.toFixed(0) + " °C (Table S7i)." : ".") + " The practical statement is therefore narrower than \"thin gaps require active cooling\": the architectures that need active thermal management are the ones that raise the transport ceiling without thinning the gap, because they leave the heat source exactly where it was while asking the cell to run an order of magnitude harder, together with the stack, whose interior cell is enclosed by its neighbours and rejects almost nothing unaided. Because these duties are computed with κ at 25 °C they are upper bounds on the true requirement, in the same sense that the ceilings of §S6.1 are lower bounds (§S6.3)."),
  p("Four accounting choices deserve explicit statement. (i) Ohmic term: V_ohm = i·L/κ is the planar (parallel-plate, 1D primary) resistance with κ from Table S4. The beaker rows use the 2 cm spacing of ordinary laboratory practice rather than 5 mm, so the gap itself is not optimistic; that is already carried in the ceilings quoted above and must not be applied a second time. What remains optimistic is the geometry: small electrodes in a large vessel carry a primary-current-distribution factor above the planar L/κ·A, so the beaker boil-off currents are still upper bounds for typical beaker practice, by a smaller margin than the 2–4× a 5 mm gap would imply. (ii) Vessel size and thermal mass: heat capacity does not enter the steady state at all — T_ss = T_amb + q/U′ contains no C — but it does not follow that boil-off is independent of cell volume, because inventory and rejecting surface are physically coupled. Scaling a vessel scales A_external, hence σ and U′; with ohmic heat ∝ i²L/κ and A_external ∝ V^(2/3), the ceiling follows i_boil ∝ V^(1/3). For DMF at a 2 cm gap over 10 cm² electrodes the passive ceiling runs " + [50, 100, 500, 1000].map(v => THERM.volume_sweep.i_boil_mAcm2.DMF[String(v)].toFixed(0)).join(", ").replace(/, ([^,]*)$/, " and $1") + " mA cm⁻² at 50, 100, 500 and 1000 mL, so a litre-scale beaker tolerates " + xmul(THERM.volume_sweep.i_boil_mAcm2.DMF["1000"] / THERM.volume_sweep.i_boil_mAcm2.DMF["100"], 2) + " the current density of the 100 mL vessel specified in §S6; the 100 mL entry is the DMF beaker ceiling of §S6.1. Statements that the ceiling is independent of inventory hold only if UA is pinned while inventory changes, which is not physically realisable; the beaker rows of §S6 are therefore specified as a 100 mL vessel (σ = " + SIG_B.toFixed(2) + ", from the wetted vessel area). Heat capacity does govern the transient, τ = m·c_p/UA, and this separates the architectures sharply: a 100 mL beaker of DMF has τ ≈ " + TAU_MIN(100).toFixed(0) + " min, whereas the 0.025 mL held in the 25 μm gap of the microfluidic archetype reaches its steady state in well under a second, passively or with active plates. Thin-gap cells therefore arrive some three orders of magnitude faster, so the thermal inertia that makes a beaker forgiving of a current excursion or a cooling interruption is absent by construction; the margins of §S6.1 are reached essentially immediately. Batch scale cuts the other way for beakers: τ grows only as V^(1/3) (≈" + TAU_MIN(100).toFixed(0) + " min at 100 mL, ≈" + TAU_MIN(1000).toFixed(0) + " min at 1 L) while the charge-limited run time grows as V, so larger batches are the more likely, not the less likely, to sit at their steady-state temperature for most of the electrolysis. (iii) Recirculating architectures: in operation the flowing electrolyte carries the heat advectively to the reservoir, so the steady state is set by rejection at the reservoir or exchanger, and a recirculating loop with its own exchanger restores a time constant of minutes (≈ " + (MCP_DMF_100 / (CF_LIQ("recirculating flow").U_hi * 10) / 60).toFixed(0) + "–" + (MCP_DMF_100 / (CF_LIQ("recirculating flow").U_lo * 10) / 60).toFixed(0) + " min for a 100 mL DMF loop through the recirculating cell's own water jacket, Table S7i) without changing U′_req. (iv) Zero-gap idealisation: the stack entry treats the 100 μm separator as a gap filled with the bulk electrolyte, which is the like-for-like comparison across solvents but neglects membrane-specific conductivity and the tortuosity of porous electrodes; it should be read as the geometric limit of gap reduction rather than as a validated non-aqueous stack design."),

  ...S12_EL(),
  h2("S6.3 Temperature dependence of conductivity"),
  p("The analysis above uses the 25 °C conductivities in Table S4, although the cells whose behaviour they predict are, by construction, approaching their boiling points — 66 °C for THF, 82 °C for MeCN, 100 °C for the aqueous reference, 153 °C for DMF. Conductivity rises with temperature, so holding κ at 25 °C overstates the ohmic heat generated at every operating point and therefore understates every boil-off ceiling. No temperature dependence of κ (or of μ) enters the thermal model, the cell-voltage stack or the transport correlations anywhere in the code. The resulting bounds are therefore one-sided: the ceilings of §S6.1 are conservative lower bounds and the cooling duties of §S6.2 are conservative upper bounds."),
  p("We bound the effect rather than correct it, because a correction would require κ(T) data we do not have for these compositions. Two effects compete as temperature rises: falling viscosity lets ions move faster, which raises κ (Walden, κ ∝ 1/μ), while the falling dielectric constant increases ion pairing, which holds κ back. A single Arrhenius or Walden law captures the first mechanism only, so it is an upper bound on the ceiling — this is also why the literature on organic liquid electrolytes reports that single-Arrhenius fits describe them poorly and that VFT-type forms are needed. The defensible statement is therefore a bracket: the lower end is κ fixed at 25 °C, the value used throughout §S6; the upper end is Arrhenius scaling of κ from 25 °C to the boiling point with an activation energy of 15 kJ mol⁻¹. That 15 kJ mol⁻¹ is a declared assumption, not a fitted or measured quantity, and its one piece of external support is an anchor on water, whose viscosity is well tabulated: μ = 0.890 cP at 25 °C and 0.282 cP at 100 °C, a ratio of 3.16, so Walden predicts κ × 3.16 at 100 °C, while Arrhenius at 15 kJ mol⁻¹ predicts × 3.37 — the two agree to 6.9%. Anything narrower than this bracket would require measured κ(T) for the specific electrolytes."),
  p("Applied at each solvent's boiling point the upper bound multiplies κ by " + listAnd(_sorder.map(x => f2(KT.solvents[x].kappa_factor_at_Tboil) + " (" + T_PRETTY[x] + ")")) + ". The unstirred-beaker ceilings of §S6.1 then move from " + _sorder.map(x => ktCeil(KT_BEAKER, x).i_boil_25C.toFixed(0) + " to " + ktCeil(KT_BEAKER, x).i_boil_kappaT.toFixed(0)).join(", ").replace(/, ([^,]*)$/, " and $1") + " mA cm⁻² respectively, and across all " + KT.factor_range.n_pairs + " (architecture, solvent) pairs of §S6.1 the bracket spans a factor of " + f2(KT.factor_range.min) + " to " + f2(KT.factor_range.max) + ". " + (KT.factor_range.n_pairs - KT_FLIPS.length) + " of those pass/fail verdicts are identical at both ends of the bracket. The " + KT_FLIPS.length + " bound-dependent verdicts are " + KT_FLIPS.map(f => ktPair(f.reactor, f.solvent)).map((d, j) => T_PRETTY[KT_FLIPS[j].solvent] + " in the " + KT_FLIPS[j].reactor.replace("$\\mu$m", "μm") + " (" + d.i_boil_25C.toFixed(0) + " → " + d.i_boil_kappaT.toFixed(0) + " mA cm⁻² against " + d.i_design.toFixed(0) + ")").join("; ") + ". Each is stated as conditional in §S6.1, and none is reported as a finding. They are exactly the four the surface-area sweep of §S6.4 flags, and the two at the rotating disc are also conditional on the gap (Table S7i), so the marginal architecture–solvent pairs are marginal on more than one axis, and no cell that clears comfortably at 25 °C is put at risk by the bracket. The qualitative conclusions — that transport binds before heat in the batch and thick-gap cells, that the two rotating archetypes cannot sustain their own transport ceilings in " + listAnd(ROT_ROBUST.map(x => T_PRETTY[x])) + " under passive cooling, that only thinning the gap raises the thermal ceiling, and that the zero-gap stack collapses on its own enclosed geometry — are robust to the omitted temperature dependence. The absolute ceilings are not, and should be read as lower bounds."),
  p("The DMF factor carries the weakest support of the four and should be treated separately. Its × 6.14 is an extrapolation of the Arrhenius coefficient across 128 K, from 25 °C to 152.8 °C, whereas the water anchor that licenses that coefficient was established across 75 K; it is also the factor that produces the largest single change in the table (" + ktCeil(KT_BEAKER, "DMF").i_boil_25C.toFixed(0) + " → " + ktCeil(KT_BEAKER, "DMF").i_boil_kappaT.toFixed(0) + " mA cm⁻² in the beaker, " + ktCeil(KT_MICRO, "DMF").i_boil_25C.toFixed(0) + " → " + ktCeil(KT_MICRO, "DMF").i_boil_kappaT.toFixed(0) + " mA cm⁻² in the microfluidic). Ion pairing in an amide solvent at 153 °C is precisely the regime in which the neglected dielectric term is largest, so the true DMF ceiling almost certainly sits well below the upper bound. No conclusion in this work rests on the DMF upper bound; it is quoted only to establish the width of the bracket. Every upper-bound number in this section is reproducible from this document alone: it is the boil-off current of Eqs. S20–S21, evaluated with exactly the geometry, σ, h_int and h_ext of §S6.1 and the Table S4 conductivity multiplied by exp[(E_a/R)(1/298.15 − 1/T_b)] with E_a = 15 kJ mol⁻¹. The full bracket for all " + KT.factor_range.n_pairs + " (architecture, solvent) pairs is computed at build time."),

  h2("S6.4 Inter-electrode gap and heat-rejection area"),
  p("Two terms in the heat balance carry no source for most of these cells: the inter-electrode gap and \u03c3. Neither is given an invented band. Each is swept and reported as a breaking point, the multiple of the declared value at which a verdict would reverse. \u03c3 is the tighter of the two, and " + TGEO.conditional_on_sigma.length + " verdicts turn over within a factor of 2.5 of it, all of them at an architecture that intensifies transport without changing the cell body. Those " + TGEO.conditional_on_sigma.length + " are stated as conditional in §S6.1. σ also scales the water jacket's coefficient, so it moves the THF liquid-cooling verdicts of §S6.2 too: no jacket in the declared construction range suffices below " + TAX_LIQ("RDE 1600 rpm").toFixed(2) + "× of it at the rotating disc or below " + TAX_LIQ("rotating cyl. 3000 rpm").toFixed(2) + "× at the rotating cylinder (Table S12)."),
  p("One of the three architectures that inherit the beaker σ (§S6.1) has external corroboration, and it runs in the safe direction. The parallel H-cell of Table S1\u00ab" + "watkins2023" + "\u00bb is a modification of the cell of Lobaccaro et al.,\u00ab" + "lobaccaro2016" + "\u00bb whose two polycarbonate compartments are drawn 2 \u00d7 2.2 in and 0.48 in thick around a 1 cm\u00b2 cathode; the two compartments alone present " + LOB_A.toFixed(0) + " cm\u00b2 of outer surface over 1 cm\u00b2 of electrode, i.e. \u03c3 \u2248 " + LOB_A.toFixed(0) + " against the " + SIG_B.toFixed(2) + " this model carries. The value used here is conservative for that cell by a factor of about " + (LOB_A / SIG_B).toFixed(0) + ", and adopting the published one would only widen a margin that already clears, so it is not adopted: one exemplar body is not the archetype, and the modified cell's own dimensions are not published. The same is not available for the other two, whose exemplars state no external dimensions, so those rows keep the beaker value."),
  p("The gap admits a weaker but independent test. The same exemplar reports a measured cell resistance of 45\u201360 \u03a9 in 0.1 M KHCO\u2083, and at the 1 cm\u00b2 cathode of the cell it was built from, with the handbook's \u03ba = 8.9 mS cm\u207b\u00b9 at 20 \u00b0C (Table S7i) carried to 9.6\u20139.8 mS cm\u207b\u00b9 at 25 \u00b0C on the same 1.5\u20131.9%/K coefficient the aqueous rows of that table use, that corresponds to an ohmic path of 0.43\u20130.58 cm. That figure is a LOWER bound on the quantity the heat balance needs and not an estimate of it: the resistance is the uncompensated value between working and reference electrodes, whereas the Joule heat is dissipated across the full working-to-counter path, which is longer. The declared 2 cm sits above the bound, so the measurement is consistent with it without pinning it. Two conditions are stated rather than buried: the exposed area is taken from the cell this one modifies, not from the modifying paper, and the bound assumes the reference sits within the cathode compartment as described."),
  p("Finally, one simplification is small here but would not be small in every cell. The balance places the internal and external films in series and carries no conduction resistance through the vessel wall between them. Through a " + (1e3 * CF.wall_conduction.L_m[0]).toFixed(0) + "–" + (1e3 * CF.wall_conduction.L_m[1]).toFixed(0) + " mm borosilicate wall (k = " + CF.wall_conduction.k_W_mK.toFixed(1) + " W m⁻¹ K⁻¹), the thickness Table S7i declares for the jacketed cell, that term lowers U′ of the cells computed on the beaker body by " + CF.wall_conduction.U_drop_pct[0].toFixed(1) + "–" + CF.wall_conduction.U_drop_pct[1].toFixed(1) + " % and their boil-off ceilings by " + CF.wall_conduction.ceiling_drop_pct[0].toFixed(1) + "–" + CF.wall_conduction.ceiling_drop_pct[1].toFixed(1) + " %, and it changes " + (CF.wall_conduction.verdicts_changed === 0 ? "none" : String(CF.wall_conduction.verdicts_changed)) + " of the " + CF.wall_conduction.n_cells + " verdicts those cells carry. No architecture in §S6 is computed on a plastic body, whose conductivity this analysis does not carry; for such a body the term would have to be restored."),
  h1("S7. Summary of limiting currents"),
  p("The full matrix applies the same physical model across all fifty rows: a one-dimensional steady Nernst–Planck balance with migration and local electroneutrality across the diffusion film, on dilute-solution theory (Newman, Ch. 11), galvanostatic; the " + numWord(N_MED) + " mediated entries and the " + numWord(SR.n_sourced) + " catalyst-carried entries with a sourced rate constant additionally carry the homogeneous EC′ source (§S5.5, §S5.7). All " + N_CELLS + " cells are converged solutions; none is reported at a numerical floor. The scope of the result follows from these assumptions: the model computes a transport ceiling, so it carries no electrode kinetics, and its film thickness is a lumped parameter from a mass-transfer correlation rather than a solved momentum boundary layer. What the migration term buys on its own, measured in the k = 0 layer against the same fifty rows solved without it, is a rise in the ≥25 mA cm⁻² count from " + ARCH.map(([lab, k]) => npCount(lab, "i_fick_mAcm2", 25) + " to " + npCount(lab, "i_np_mAcm2", 25) + " (" + ARCHLBL[k] + ")").join(", ") + ", and in the ≥50 mA cm⁻² count from " + ARCH.map(([lab, k]) => npCount(lab, "i_fick_mAcm2", 50) + " to " + npCount(lab, "i_np_mAcm2", 50) + " (" + ARCHLBL[k] + ")").join(", ") + "; the further rise to the counts of Table S5 is the homogeneous EC′ step of the mediated and sourced catalyst-carried rows. The term is not uniformly important: " + MIG.neutral + " of the 50 carriers are neutral, and migration changes the ceiling by less than 5% on " + MIG.lt5 + " of the 50 rows and roughly doubles it (up to ×" + MIG.max.toFixed(2) + ") on " + numWord(MIG.dbl) + ", each an anion oxidized in its own salt." + " Every mediated EC′ value in Table S6 is a concentration-control plateau except the " + numWord(WALL.length) + " cells published at their k = 0 floor (§S5.5), and §S5.5 measures the answer to move by at most " + G12_TXT + "% under a 7.5× finer continuation and a doubled mesh" + (() => { const near = EC.filter(c => [25, 50].some(t => Math.abs(c.ec - t) / t * 100 <= G12_MAX)); if (near.length) throw new Error("S10 says solver refinement cannot move a count, but " + near.length + " mediated cells sit within " + G12_TXT + "% of a threshold"); return ""; })() + ", and no mediated cell sits that close to 25 or 50 mA cm⁻², so solver refinement cannot move these counts in either direction. A second and larger source of imprecision in these integers is not the solver but the property inputs: " + numw(SP.n_flagged) + " of the fifty rows run in a solvent whose viscosity and density are not both measured on that medium — the two HFIP rows (viscosity measured, Krumgalz 1983, Table 3, p. 578; density from a supplier's specification) and " + numw(SP.n_flagged - 2) + " mixed-solvent rows, whose properties are derived from measured mixture data or estimated by a mixing rule (Table S7b). Because i_lim ∝ μ^p with p between −1 and −5⁄6 — exactly −1 for the five archetypes whose δ is a fixed film, and −5⁄6 and −0.988 for the Levich and Eisenberg correlations, where scaling μ moves ν and therefore δ as well and the two partly cancel — a ±25–50% error confined to those rows shifts each architecture's ≥25 mA cm⁻² count by at most " + numw(SP.worst_count_movement) + " entries of fifty (" + SP.baseline_per_arch.join("–") + " spans " + spSpan() + ") and " + (SP.substrate_span[0] === SP.substrate_span[1] ? "leaves the substrate-carried clearing count at " + SP.substrate_span[0] + " of " + SP.n_substrate : "moves the substrate-carried clearing count from " + SP.substrate_span[0] + "/" + SP.n_substrate + " to " + SP.substrate_span[1] + "/" + SP.n_substrate) + ". **The counts should therefore be read as ±" + SP.worst_count_movement + " of 50, not as exact integers.** What does not move is the ordering, " + ORDERING_TEXT + ", which holds at every point of that sweep, and every conclusion drawn here rests on the ordering and on the order-of-magnitude span, not on the individual counts "),
  mkTable(["Reactor archetype","median i_lim (mA/cm²)","≥ 25 mA/cm²","≥ 50 mA/cm²"],
    ARCH.map(([label, k]) => [label, med(k), ge25(k), ge50(k)]),
    [2500,2100,1300,1300]),
  cap("Table S5. Results across the 50-reaction set at the reported conditions of Table S2 (the Stage-1 Nernst–Planck solve, with migration, for direct entries and for the " + numWord(SR.n_floor) + " catalyst-carried entries with no sourced rate constant; EC′ solver for the mediated entries and for the " + numWord(SR.n_sourced) + " catalyst-carried entries carried at a sourced rate constant, §S5.7). The " + N_NEVER25 + " reactions below the 25 mA cm⁻² threshold in every architecture are the concentration-capped core: " + CAT_FRAC_THE() + " catalyst-carried entries (" + CAT_NEVER_mM + " mM at the reported loadings; " + numWord(SR.n_sourced) + " of the class at a sourced rate constant and " + numWord(SR.n_floor) + " at k = 0, §S5.7), three mediated entries (the 25 mM ACT mediator, which tops out at " + ACT_TOP + " mA cm⁻²; the oxygen-mediated Giese addition, carried by " + CARR_mM.get("Cathodic Giese (R-I + alkene)").toFixed(2) + " mM dissolved oxygen; and the " + mMfmt(CARR_mM.get("Oxazole synthesis from ketones and acetonitrile")) + " mM triarylamine of the oxazole synthesis, solved at k = 0), and two substrate-carried entries (a 0.02 M flow-kinetics study and the radical-cation Diels–Alder chain, tabulated at the 0.1 F mol⁻¹ it passes). The single catalyst-carried entry that clears threshold is the " + CAT_CLEAR_mM + " mM Ni aryl–aryl homocoupling (ref. ⟦courtois1997⟧); the kilogram-scale flow XEC system (ref. ⟦kelly2026⟧), verified at 15 mM Ni, is carried at the sourced k = 10² M⁻¹ s⁻¹ at the DMA viscosity CRC prints (1.927 mPa s, p. 6-244; a printed value that disagrees with its own homolog by a factor of two, Table S7b). " + ckXec() + " At k = 0 the same row's ceiling is " + srRow("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)").i_k0_mAcm2.rce.toFixed(1) + " mA cm⁻² in the rotating-cylinder cell and " + srRow("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)").i_k0_mAcm2.flow.toFixed(1) + " in the recirculating-flow cell, below the current the campaign ran at; the difference is the homogeneous step, not the viscosity."),
  p("These thresholds are anchored in the pharmaceutical-industry survey of Ferretti et al.«ferretti2025» (17 companies surveyed): of the 14 that reported scale-up current densities (Fig. 11 therein), 10 operate below 25 mA cm⁻², three between 25 and 50, and one above 50 mA cm⁻². The model reproduces this operating reality and locates its cause: at the reported exemplar concentrations (modern academic scope rows cluster at 0.02–0.5 M; preparative-scale and industrial entries run 0.8–6.9 M), batch and standard flow reactors place the transport ceiling on the order of tens of mA cm⁻², the same order as the reported industrial operating window. This comparison is intentionally order-of-magnitude. The measured stirred-cell film of 200 \u00b1 7 \u03bcm gives a median of " + med("stirred") + " mA cm\u207b\u00b2, but the overlapping unstirred-film range does not support a sharper distinction between the two batch archetypes. A direct measurement provides the more relevant bound. Williams and co-workers measure the mass-transport boundary layer of a gas-bubbled electrochemical cell from the diffusion-limited ferricyanide current through i_lim = nFDc/\u03b4, and convert it to dissolved O\u2082 by the ratio of the two diffusivities, obtaining 200 \u00b1 7 \u03bcm (Sustain. Energy Fuels 2019, 3, 1225, p. 1228). That is a planar electrode in a convecting cell, the same situation as this archetype, and O\u2082 diffuses about " + O2PROXY.ratio + " times as fast as the median carrier modelled here. A convective film thickens with the diffusivity (\u03b4 \u221d D^\u2153 for a laminar boundary layer, D^\u00bd under penetration theory), so the organics' own layer should if anything be thinner than O\u2082's, by roughly " + O2PROXY.lo + "\u2013" + O2PROXY.hi + "%. This measurement is the value the archetype uses, so the stirred ceilings rest on a measured film rather than an estimated one, and the direction of its residual error is known: a thinner true layer would raise them, so they are conservative. What it does not resolve is which batch archetype a claim would belong to, since the free-convection band for the unstirred cell overlaps it. Evaluating Levich \u03b4 = 1.61 D^1/3 \u03bd^1/6 \u03c9^\u22121/2 on each reaction\u2019s own D and \u03bd gives row medians of 15\u201336 \u03bcm across 200\u20131200 rpm, an order of magnitude below the measurement; that is the correct behaviour of a rotating disc, which is a uniformly accessible electrode in the most efficient laminar convection available, and it is not what a stationary plate in a stirred beaker sees. The idealised bound therefore sits an order of magnitude below the value in use, as it must, and the measurement is what the archetype rests on. A film thin enough to put the stirred median above 25 mA cm\u207b\u00b2 would have to be " + STIR_THIN.toFixed(1) + " times thinner than the measured cell, which nothing here brings within reach. Because the stirred and recirculating-flow archetypes are both fixed films, a \u03b4_stirred below the flow cell's " + FLOW_FILM_UM + " μm would raise every stirred ceiling above its flow counterpart and invert the first steps of the ordering this section rests on. That is a self-consistency argument, not evidence, and it is labelled as such. Crossing the 50 mA cm⁻² barrier that only one surveyed company has broken requires nothing more than the thin-film reactor architectures of Table S5: " + ge50("natural") + " reactions clear it in an unstirred cell, " + ge50("rce") + " at a rotating-cylinder electrode, with the chemistry and concentrations unchanged."),
  p("The carrier decomposition is the central mechanistic result: convection engineering rescues substrate-carried chemistry essentially without exception, while dilute-carrier chemistry is concentration-capped in every reactor — by the carrier where the homogeneous step is slow and by the dilute substrate where it is fast, with the " + numWord(SR.n_sourced) + " rows carried at a sourced rate constant sitting between the two, mostly in the kinetic regime (substrate-limited in the thickest films), where thinning the film buys a few-fold rather than the 1/δ of a transport-limited row (§S5.7). Raising the ceiling for that class requires raising the carrier concentration itself or decoupling the electrode event from the catalytic cycle (paired/ex-cell schemes). The one gas-fed substrate in the set, ethylene in the chloride-mediated epoxidation, is solubility-limited only inside the film: that row's ceiling is set by the chloride carrier, and most of the oxidant the carrier makes reacts in the bulk (§S4, §S5.5)."),

  h1("S8. Limitations"),
  p("The parameter table quantifies the data problem the main text describes: of the 50 diffusivities, " + (DPROV.wc + DPROV.se) + " are correlation estimates (" + DPROV.wc + " Wilke–Chang, " + DPROV.se + " Stokes–Einstein), " + DPROV.ne + " rest on measured limiting conductivities (Nernst–Einstein, " + numWord(DPROV.walden) + " of them carried to its solvent by Walden's rule) and " + numWord(DPROV.meas) + " is measured (dissolved O₂ in water, Cussler, Table 5.2-1, p. 127); none of the non-aqueous organic values has a direct experimental measurement in its actual working electrolyte. Concentrations are representative of exemplar reports rather than optimized values; activity corrections, ion pairing in low-ε solvents, and concentration-dependent viscosity are all outside dilute-solution theory; and the two batch films rest on one measurement in a comparable cell and one correlation (Table S1), not on measurements in these reactors. None of these caveats disturbs the architecture ranking from the stirred cell upward or the carrier dichotomy, which rest on ratios spanning one to two orders of magnitude, but all of them limit reaction-by-reaction precision. Machine-learned property prediction (e.g., Chemprop-class models trained on the sparse measured D data) and standardized reporting of D, κ, and solubility alongside synthetic results would upgrade this screening model into a quantitative design tool; the continuum frameworks developed for CO₂ electrolysis«bui2022» then translate directly."),
  p("The provenance registry of Table S7 makes that data problem quantitative rather than rhetorical, and its result belongs in the same place. Of the " + CENSUS_ALL.n + " registered parameters, " + CENSUS_ALL.measured + " are measured with a specific source locator, " + CENSUS_ALL.derived + " are derived from measured or derived inputs by a named method, and " + CENSUS_ALL.assumption + " are declared assumptions with a stated sensitivity. (These four counts, and every other census figure in this document, are generated from the registry at build time to maintain consistency between the prose and tables.)" + " This appendix tabulates the parameters that can support a stated claim, figure or table entry: " + N_OMITTED + " further rows are carried in the machine-readable registry and omitted here. They are omitted by a stated rule rather than by selection — a row is set aside when the solvent it describes is used by none of the fifty reactions, or when its own registry text declares it display-only — and the rule is applied mechanically, and it also asserts that nothing load-bearing can be caught by it: no solver species, no conductivity carrying a §S6 verdict, and no solvent any reaction uses. The distinction is worth making because the union of the two sets misrepresents the weakest category. Counting every row, the electrolyte conductivities read " + CENSUS_COND_ALL.measured + " measured, " + CENSUS_COND_ALL.derived + " derived and " + CENSUS_COND_ALL.assumption + " assumption, which invites the conclusion that the ohmic and thermal analysis rests on that many unsourced numbers. It rests on four, and those four are the ones tabulated in Table S4 with the margin by which each would have to be wrong to overturn the verdict it carries. A fifth survives the filter for a different reason: 0.1 M Bu₄NBF₄ in DMF is quoted in the main text rather than used by any entry of the fifty, and is registered here so that the worked example built on it can be checked. The remaining conductivities are attached to reactions but drive nothing that is reported here, because κ enters no transport quantity: Eq. S1 and the Nernst–Planck and EC′ solvers use D, C, δ and z only." + (LEDGER ? " That last figure is the one most open to misreading, so it is broken out rather than left as a total. Sorting the " + LEDGER.n_assumption_live + " state-C rows of this appendix by what actually backs each one: " + [(LEDGER.counts_live.T0 ? LEDGER.counts_live.T0 + " are consumed but a named gate establishes they cannot move a reported conclusion" : null), (LEDGER.counts_live.T1 ? LEDGER.counts_live.T1 + " are declared choices rather than measurements of anything \u2014 " + LEDGER_T1_TXT() + " \u2014 validated by convergence and sweep studies because no citation could support them" : null), (LEDGER.counts_live.T2 ? LEDGER.counts_live.T2 + " state a perturbation and its computed effect, and the conclusion survives the stated range" : null), (LEDGER.counts_live.T3 ? LEDGER.counts_live.T3 + " do the same but the row itself records that a conclusion is conditional on where the value sits in its band, and those are the rows to read first" : null), (LEDGER.counts_live.T4 ? LEDGER.counts_live.T4 + " give no magnitude but fix the sign, so that no magnitude of the term could reverse the inequality claimed" : null), (LEDGER.counts_live.T5 ? LEDGER.counts_live.T5 + " fail the standard\u2019s own test of carrying a perturbation and its effect" : null)].filter(Boolean).join("; ") + ". " + (LEDGER.counts_live.T5 ? "" : "No row of this appendix fails that test. ") + "The classification is derived from the registry text by a published rule rather than assigned row by row, and the rule is checked in both directions: a blanked sensitivity, a bare cross-reference and the unsupported word \u201cconservative\u201d all fall to the lowest class." : "") + " The assumptions are not evenly spread. Of the " + CENSUS_COND.n + " electrolyte conductivities this appendix publishes, " + CENSUS_COND.measured + " are measured, " + CENSUS_COND.derived + " derived and " + CENSUS_COND.assumption + " an assumption, which still leaves the conductivity of a preparative organic electrolyte the hardest number in this work to source. So are "  + CENSUS_DIFF.assumption + " of the " + CENSUS_DIFF.n + " entries of the solver-species block (Table S7d), most of them diffusivities in non-aqueous or mixed media, and every mixture viscosity and density except " + MIX_DERIVED_TXT + " (Table S3). Several thermal inputs carry no citation and are declared assumptions for that reason — the separator gap, surface-area ratio and reference current of the zero-gap stack, and the surface emissivity — each given in Table S7i with a sensitivity in place of a reference; the liquid-cooling coefficient, by contrast, is derived from laminar internal-flow heat transfer. The two batch films are not of that kind: the stirred film is measured in a comparable convecting cell, and the unstirred film is derived from a published free-convection correlation and corroborated by a measurement (Table S1). The concentrated aqueous conductivities are cited to \"Electrical Conductivity of Aqueous Solutions\", CRC Section 5, p. 5-71, which tabulates 0.5–50 mass %; the equivalent-conductivity table at p. 5-74 is at 25 °C and stops at 0.1 M, so it cannot reach these concentrations. On that basis " + AQ_COND_TXT + " (§S6.1, Table S4). Where a conclusion turns on where an input sits in its band, it is stated conditionally where it is drawn (§S6.2), and its registry row says so in Table S7. What survives is what the analysis was for: an architecture ranking and a carrier dichotomy that rest on ratios of one to two orders of magnitude, and that are stable across every sensitivity band in Table S7 except one: the order of the two batch archetypes turns on the declared free-convection operating point (Table S7g)."),
  h2("S8.1 Conversion per pass and pressure drop"),
  p("A limiting current density is a flux, and the quantities that decide whether a reactor is "
    + "useful are a productivity and the cost of achieving it. Those move differently from the "
    + "flux, and in one case they move in the opposite direction, so they are computed here for "
    + "a declared pair of generic laminar parallel-plate channels \u2014 1 mm / 5 cm / "
    + "5 cm s\u207b\u00b9 and 250 \u00b5m / 2.5 cm / 10 cm s\u207b\u00b9 (Table S7g) \u2014 chosen to span a "
    + "fourfold gap step; none of the archetypes of Table S1 is computed from them, and the "
    + "L\u00e9v\u00eaque correlation that describes them is the one the microfluidic archetype's "
    + "half-gap floor is checked against. Residence time is \u03c4 = L/u; conversion per pass for plug flow with a "
    + "wall sink and specific area a = 1/h is X = 1 \u2212 exp(\u2212k_m\u03c4/h); the laminar "
    + "pressure drop between parallel plates is \u0394P = 12\u03bcuL/h\u00b2. At the median carrier diffusivity of the 50-reaction set the two channels give \u03b4 = " + f2(reA.delta_um) + " and "
    + f2(reB.delta_um) + " \u00b5m, \u03c4 = " + f2(reA.tau_s) + " and " + f2(reB.tau_s) + " s, "
    + "conversion per pass " + f2(100*reA.conversion_per_pass) + "% and "
    + f2(100*reB.conversion_per_pass) + "%, and \u0394P = " + f2(reA.dP_Pa/1000) + " and "
    + f2(reB.dP_Pa/1000) + " kPa."),
  p("Comparing the 1 mm and 250 \u00b5m channels shows that thinning the gap changes these "
    + "quantities differently. The thinner gap lowers \u03b4 by " + f2(reR.delta)
    + "\u00d7 and raises flux by approximately the same factor. Although the residence time "
    + "decreases by " + f2(1/reR.tau) + "\u00d7, the specific area a = 1/h increases by the "
    + "same factor, so conversion per pass rises by " + f2(reR.X_pass) + "\u00d7. The tradeoff "
    + "is pumping: \u0394P scales as 1/h\u00b2 at fixed velocity and rises " + f2(reR.dP)
    + "\u00d7. Gap reduction therefore improves both flux and conversion per pass in this "
    + "comparison, while increasing pressure drop and fabrication demands."),
  p("Two cautions attach to these numbers. Plug flow with a wall sink overstates conversion "
    + "relative to a real velocity profile, which is the direction that does not flatter "
    + "intensification; and \u0394P is the fully developed laminar result, excluding entrance "
    + "effects and manifolding, so it is a lower bound on real pumping cost. Both single-pass "
    + "conversions are small in absolute terms \u2014 under 5% \u2014 which is why flow cells in this "
    + "field are run with recirculation rather than in a single pass, and why a per-pass number "
    + "should never be read as a batch yield."),

  ...s9,

  h1("S10. Bounds on reported quantities"),
  p("Each quantity reported in the main text is given below with a lower and an upper bound, obtained by recomputing it at the limits of the range declared for its dominant input. The model is re-evaluated at those limits rather than linearised about the central value."),
  p("Transport and thermal quantities are bounded differently because they scale differently. For the seven architecture medians and the \u226525 and \u226550 mA cm\u207B\u00B2 counts the dominant input is the diffusion-layer thickness, taken over \u03B4 = " + DB_NAT[0].toFixed(0) + "\u2013" + DB_NAT[1].toFixed(0) + " \u03BCm (unstirred, the free-convection envelope over the declared height and driving force, taken at the extreme rows of the set), 193\u2013207 \u03BCm (stirred, the measurement\u2019s own uncertainty), \u00b112.1 % about the measured 106.9 and 36.2 \u03BCm (recirculating and ANEC flow cells, the replicate scatter the same study reports for its one replicated cell), the printed residence-time range 4\u201312 min (microfluidic cell, over which the half-gap film does not move), 400\u20133600 rpm (RDE) and 1000\u20135000 rpm (rotating cylinder). For the " + (50 - N_MED - SR.n_sourced) + " reactions treated by the Nernst\u2013Planck film model alone i_lim \u221D 1/\u03B4 exactly, so those columns rescale with \u03B4. For the " + numWord(N_MED) + " mediated entries and the " + numWord(SR.n_sourced) + " catalyst-carried entries at a sourced rate constant it does not: the catalytic amplification i_ec/i_t0 depends on \u03B4/x_k and varies by up to " + BANDAMP.toFixed(1) + "-fold between the two \u03B4 limits of one architecture, so each is re-solved at both limits."),
  p("For the Fig. 7 boil-off ceilings and zero-gap currents the dominant input is the electrolyte conductivity, taken over the band given for each electrolyte in Table S4; the cooling-duty ratios of the rotating cells and the stack move as much with their operating current (rotation rate, current density), and Table S12 lists where each cooling class changes. Two further model choices widen those bands: the internal film coefficient h_int, over 50 W m\u207B\u00B2 K\u207B\u00B9 to the well-stirred limit, moves " + hintSentence() + ", and the cooling shortfalls of Table S9 are bounded over the same h_int sweep as well as the κ band; and evaluating the external film at the boiling point rather than at 65 \u00B0C changes the unstirred-beaker ceilings by " + ["THF", "MeCN", "DMF", "aq. NaOH"].map(n => { const v = BOUNDS.h_ext_T_pct[n]; return (v < 0 ? "\u2212" : "+") + Math.abs(v).toFixed(1) + "% (" + (n === "aq. NaOH" ? "aqueous NaOH" : n) + ")"; }).join(", ").replace(/, ([^,]*)$/, " and $1") + "; the upper edges of the Table S9 ceilings evaluate the external film at the boiling point in each cell, together with the \u03ba band and the h_int sweep."),
  p("One bound is one-sided. The conductivity of 3.0 M LiBr in THF has a hard floor, the 0.206 mS cm\u207B\u00B9 that the cell resistance of Lee et al. sets, and no measurement bounds it from above at the working concentration. The lower bound on the THF ceilings is therefore a floor rather than a limit; the THF verdicts that fail reverse only above " + THF_BIND[1].kappa_reverse_mScm.toFixed(1) + " mS cm\u207B\u00B9 (the " + ARCH_SHORT(THF_BIND[0]) + ")."),
  mkTable(["Reported quantity", "Lower", "Reported", "Upper", "Input varied"],
    Object.keys(BOUNDS.transport).map(k => {
      const v = BOUNDS.transport[k];
      const m = k.match(/^(median|count >=\d+), (\w+)$/);
      const nm = m ? (m[1].startsWith("median") ? "median i_lim, " : "count clearing " +
                      m[1].replace("count >=", "") + " mA cm\u207B\u00B2, ") + ARCHLBL[m[2]] : k;
      return [nm, bnum(v.lower), bnum(v.value), bnum(v.upper), "diffusion-layer thickness \u03B4"];
    }), [4200, 1300, 1300, 1300, 3600]),
  cap("Table S8. Bounds on the transport quantities of the main text, evaluated with every architecture at the current-minimising and current-maximising limit of its \u03B4 range. Medians in mA cm\u207B\u00B2; counts out of 50."),
  mkTable(["Reported quantity", "Lower", "Reported", "Upper", "Input varied"],
    Object.keys(BOUNDS.thermal).map(k => {
      const v = BOUNDS.thermal[k];
      return [k + (v.one_sided ? " (one-sided)" : ""), bnum(v.lower), bnum(v.value), bnum(v.upper),
              "\u03BA of " + v.registry_row.replace(/ \(.*/, "") + (/h_int/.test(v.driver) ? "; h_int" : "") + (/h_ext/.test(v.driver) ? "; h_ext at T_b (upper edge)" : "")];
    }), [4200, 1300, 1300, 1300, 3600]),
  cap("Table S9. Bounds on the thermal quantities of Fig. 7. Ceilings and zero-gap currents in mA cm\u207B\u00B2; cooling shortfalls are the ratio U\u2032_required(i_design)/U\u2032_passively available. Rows marked one-sided have a hard floor on the conductivity but no upper bound: for a ceiling row the floor sets the Lower value, which is a bound, and the Upper is not; for a cooling-shortfall row the floor sets the Upper value, which is the bound, and the Lower is not."),
  p("Three features of these bounds bear on how the results should be read. The architecture ranking is stable in the sense the analysis uses: the central medians are ordered " + ORDERING_TEXT + ", and it is that ordering, not the individual values, that the analysis rests on" + (ORD_BREAK.length ? ". Taken at the limits of their bands, " + listAnd(ORD_BREAK.map(([a, b]) => "the " + ORD_NAME[a] + " and " + ORD_NAME[b] + " medians overlap (upper limits " + BM(a, "upper") + " and " + BM(b, "upper") + " mA cm\u207B\u00B2)")) + ", because the free-convection film is uncertain enough to reach the stirred film (Table S1)" : ", and it holds at both limits of every band") + ". The three thin-film medians lie within " + Math.round(100 * (Math.max(...ORDER_THIN.map(k => MS.get(k).median)) / Math.min(...ORDER_THIN.map(k => MS.get(k).median)) - 1)) + "% of one another and are not claimed to be ordered among themselves; the rotating-disc/rotating-cylinder pair is the one the second correlation of §S3.3 inverts, and that is disclosed there. The counts are less stable \u2014 the \u226525 mA cm\u207B\u00B2 count in an unstirred cell spans " + bnum(BOUNDS.transport["count >=25, natural"].lower) + "\u2013" + bnum(BOUNDS.transport["count >=25, natural"].upper) + " of 50 about a central " + bnum(BOUNDS.transport["count >=25, natural"].value) + ", and the stirred count " + bnum(BOUNDS.transport["count >=25, stirred"].lower) + "\u2013" + bnum(BOUNDS.transport["count >=25, stirred"].upper) + " about " + bnum(BOUNDS.transport["count >=25, stirred"].value) + " \u2014 so a count indicates the order of how many reactions are transport-limited rather than a precise tally. And the microfluidic cell clears by a wide margin on this axis too: the cooling duty DMF needs there spans " + bnum(BOUNDS.thermal["DMF 25 um cooling shortfall"].lower) + "\u2013" + bnum(BOUNDS.thermal["DMF 25 um cooling shortfall"].upper) + " times what that cell rejects unaided, so passive cooling suffices across the whole conductivity band."),
  p((() => {
    // Computed from results/substrate_D_sensitivity.json (2026-09-14). This paragraph typed the
    // bromination cell at 25.3 mA cm-2 and a 12 -> 11 count move from the 300 um unstirred film;
    // on the 228 um film that cell reads 33.3 and the sweep moves different counts.
    const SD = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "substrate_D_sensitivity.json"), "utf8"));
    const moves = [];
    SD.scales.forEach(sc => Object.keys(SD.base_counts).forEach(a => [0, 1].forEach(t => {
      const b = SD.base_counts[a][t], v = SD.counts[String(sc)][a][t];
      if (v !== b) moves.push(a.replace(/ \(25 um gap\)/, "").replace(/^(Recirculating|Unstirred|Stirred|Microfluidic|Rotating)/, w => w.toLowerCase()) + " \u2265" + (t ? 50 : 25) + " mA cm\u207B\u00B2 count " + b + " \u2192 " + v + " of the " + numWord(N_MED) + " at \u00D7" + sc);
    })));
    const cc = SD.closest_cell_to_25;
    return "A further sensitivity acts through a different input: the substrate diffusivities of the " + numWord(N_MED) + " mediated entries, which are Wilke\u2013Chang estimates apart from one measured value. Scaling all " + numWord(N_MED) + " together by \u00D7" + SD.scales[0] + " and \u00D7" + SD.scales[1] + " and re-solving the mediated matrix "
      + (moves.length ? "moves " + moves.join("; ") + ", and no count by more than one entry" : "moves no count")
      + ". The mediated cell closest to 25 mA cm\u207B\u00B2 is " + cc.reaction.replace(" -> ", " \u2192 ") + " in the " + cc.reactor.replace(/ \(25 um gap\)/, "").toLowerCase().replace("microfluidic cell", "microfluidic cell") + " at " + cc.i_mAcm2.toFixed(1) + " mA cm\u207B\u00B2, " + cc.margin_pct_to_25.toFixed(1) + "% above the threshold.";
  })()),

  h1("S11. Construction of the main-text figures"),
  p("Each main-text figure is computed from the inputs and results tabulated in this SI, re-plotted from a published data table, or drawn as a schematic. This section gives the source of every panel."),
  p("**Figure 1.** Panels (a)–(c) are computed from the dataset of §S4.1. Panel (a) counts distinct transformations by the earliest reported year retained on deduplication, per year and cumulatively. Panel (b) sorts the atom-mapped records into the transformation classes of §S4.1 and divides each class by the net redox change of its substrate ledger. Panel (c) gives, among the records that report each field, the share run in an undivided cell, under constant-current control, and by direct rather than mediated electron transfer; mediation is identified from each record's reagent and catalyst entries, so the mediated share is a lower bound. Panel (d) is a four-step funnel on logarithmic widths: the dataset total, the reactions demonstrated at 20 g or more reported by Lehnherr and Chen«lehnherr2024», the kilogram-scale pharmaceutical programmes reported by Kelly et al.«kelly2026», and the absence of a commercialized process among the companies surveyed by Ferretti et al.«ferretti2025»"),
  p("**Figures 2, 3 and 8** are schematics drawn for this work. Figure 2 summarises the interfacial mechanisms of main-text Section 2.1 and Figure 8 the component-level failure modes of Section 6; neither asserts a magnitude. Figure 3 summarises the case studies of Section 2.2, whose sources are cited there."),
  p("**Figure 4.** Panel (a) is a schematic of the reactor archetypes. Panel (b) places each of the seven modelled architectures at the median, over the fifty reactions, of its diffusion-layer thickness from the correlations and measured films of Table S1, against its median limiting current from Table S5. Panel (c) is a Nernst–Planck solve (§S5.1) of " + PROFILE_CASE + " on the stirred-batch film, drawn at a sequence of applied currents approaching its limiting current."),
  p("**Figure 5.** Panel (a) solves the Nernst–Planck problem of §S5.1 for " + PROFILE_CASE + " on the film of six architectures (all but the rotating disc, whose film is close to the rotating cylinder\u2019s), at 50 mA cm⁻² where a steady state exists and at the architecture's own limiting current where it does not; dashed curves mark the latter. Panel (b) plots the limiting current of every reaction in every architecture from the matrix of Table S5, coloured by carrier class; the mediated and catalyst-carried entries are the EC′ solves of §S5.5 and §S5.7. " + fig5Clip().text + ""),
  p("**Figure 6.** Panels (a)–(c) are schematics. Panels (d)–(f) are EC′ solves (§S5.4) of three mediated entries of Table S6 at their rate constants (Table S11) on the ANEC film of Table S1, drawn at the limiting current; the regime named on each panel is read from the solve, and the grey curve is the local reaction rate per unit of ln x, k·c_ox·c_S·x/(s_ox·i/F). Panel (g) repeats those three solves across the archetype films, and panel (h) does the same for three catalyst-carried entries at the rate constants of §S5.7."),
  p("**Figure 7.** All four panels are computed from the lumped energy balance of §S6.1, using the thermal parameters of Table S7i and the conductivities of Table S4. No single reaction is modeled: heat is generated only by the ohmic and electrode-overpotential terms of Eq. S20, with the illustrative electrode kinetics of Eq. S18, in each of the four electrolytes of Table S4, and each preparative architecture is run at its median limiting current from Table S5 (the zero-gap stack at its declared 1 A cm⁻²). Panel (a) is the steady-state temperature against current density in the unstirred beaker, with each organic electrolyte's boil-off current marked at its boiling point (the aqueous reference boils off above the plotted range). Panel (b) divides each architecture's boil-off ceiling by its median limiting current from Table S5. Panel (c) evaluates the boil-off ceiling across interelectrode gaps at one declared heat-rejection geometry. Panel (d) is the heat-rejection coefficient required to hold each of the five architectures from the recirculating flow cell onward at its limiting current without boiling (§S6.2), marked against what that cell rejects passively and, as grey bars, against the range its own liquid cooling supplies."),
  p("**Figure 9.** Panels (c) and (d) re-plot the per-device yields that Górski et al.«gorski2025» tabulate in their supporting information; the mean, standard deviation and per-device current are recomputed from that table and reproduce the summary that work prints, with the current taken at unit Faradaic efficiency and two electrons per bromination as it states. Panel (a) is a schematic of the device and panel (b) the assay reaction under that work's conditions."),
  p("**Figure 10.** Panel (a) redistributes the counts of Figure 1(d) across the readiness ladder of main-text Section 9, with the industrial processes named in the main text on the top rungs. Panel (b) is the architecture summary of Table S5: the median limiting current of each architecture against the 25 mA cm⁻² threshold."),

  h2("Code and data availability"),
  p("All calculations in Sections S1\u2013S10 other than the dataset statistics of \u00a7S4.1\u2013S4.2, including the transport, EC\u2032, and thermal models and every figure in Section 4, use only the inputs tabulated in this SI and require no restricted data. The transport solvers use only the Julia standard library; the thermal balance and the conductivity reconstructions use NumPy and pandas, and the Le Bas volumes and the Table S10 balances use RDKit. Main-text Figure 1 is subject to a separate data-access limitation. It was generated from reaction-level records derived from CAS content accessed through SciFinder under a limited data use agreement, which permits publication of aggregate statistics and the rendered figure but not the underlying per-record data. Independent verification is therefore possible for the aggregate outputs, including the dataset size (25,941 distinct transformations), the class counts and polarity shares in Fig. 1b, the condition fractions in Fig. 1c, and the funnel counts in Fig. 1d. The deterministic pipeline reproduces these outputs in a pinned environment (Python 3.13, RDKit 2026.3.5, pandas 3.0.5, NumPy 2.5.1, PyArrow 25.0.0); the RDKit version is specified because 20 of 21,459 polarity labels change on an earlier release. Table S2, Table S7, and all parameter counts reported in the text are generated from the same two CSV files to maintain consistency between the prose and the tabulated data."),
  h1("References"),
  ...REFS.map((r, i) => new Paragraph({
    children: [new TextRun({ text: (i + 1) + "  ", size: 18, font: "Calibri" }),
               ...r.s.map(sg => new TextRun({ text: sg.t, size: 18, font: "Calibri", italics: !!sg.i, bold: !!sg.b }))],
    spacing: { after: 40 }, indent: { left: 420, hanging: 420 } })),
];

if (SI_MODE !== "condensed") auditRefOrder();


// ---- sentence splitter shared by the condensed build and its inventory (2026-09-14) ----------
// Splits prose at sentence ends without breaking on abbreviations, initials or decimals, so the
// condensed SI can keep whole sentences of the detailed one verbatim.
const ABBR = ["e.g", "i.e", "et al", "Fig", "Figs", "Eq", "Eqs", "ref", "Ref", "refs", "vs", "ca", "cf", "p", "pp", "No", "vol", "Vol", "ed", "Ch", "Sect", "cyl", "prio", "approx", "Chem", "Soc", "Am", "J", "Int", "Ed", "Res", "Dev", "Eng", "Sci", "Lett", "Commun", "Acta", "Phys", "Trans", "Data", "Org", "Process", "Electrochem", "Rev", "Nat", "Energy", "Environ", "Mater", "Ind", "Bull", "Ser", "Univ", "Proc", "Acc", "Soln", "Solution", "Faraday", "Z", "Angew", "Adv", "Front", "Curr", "Opin", "Catal", "Green", "Sustain", "Biomol", "Annu", "Heat", "Mass", "Transfer", "Fuels", "Sources", "Power", "Kagaku", "Kogaku", "Appl", "Mol", "Chim", "Ref", "Stand"];
function splitSentences(text) {
  const out = []; let start = 0;
  const re = /([.!?])(["”’»⟧)]*)\s+(?=[A-Z(«"“0-9†‡§*Λλκδσμ])/g; let m;
  while ((m = re.exec(text)) !== null) {
    const end = m.index + 1 + m[2].length;
    const before = text.slice(start, m.index);
    const lastTok = (before.match(/([A-Za-z]+)$/) || [])[1] || "";
    if (m[1] === "." && (ABBR.includes(lastTok) || /(^|[\s(])[A-Z]$/.test(before) || /\d$/.test(before) && /^\d/.test(text.slice(re.lastIndex)))) continue;
    out.push(text.slice(start, end)); start = re.lastIndex;
  }
  if (start < text.length) out.push(text.slice(start));
  return out;
}
if (process.env.SI_SENTENCES) {
  const inv = [];
  [["front", front], ["tableS2", tableS2], ["back", back]].forEach(([part, arr]) => arr.forEach((el, i) => {
    if (el.__kind === "p" || el.__kind === "cap") inv.push({ part, i, kind: el.__kind, s: splitSentences(el.__t) });
    else inv.push({ part, i, kind: el.__kind || "raw", t: (el.__t || "").slice(0, 120), cells: el.__cells });
  }));
  fs.writeFileSync(process.env.SI_SENTENCES, JSON.stringify(inv, null, 1));
}

if (process.env.SI_INVENTORY) {
  const inv = [];
  [["front", front], ["tableS2", tableS2], ["back", back]].forEach(([part, arr]) => arr.forEach((el, i) =>
    inv.push({ part, i, kind: el.__kind || "raw", lvl: el.__lvl || 0,
               len: (el.__t || "").length + (el.__cells || "").length, t: el.__t || "" })));
  fs.writeFileSync(process.env.SI_INVENTORY, JSON.stringify(inv, null, 1));
}

// ================================================================================================
// CONDENSED SI (SI_MODE=condensed), 2026-09-14.
// Author: "a condensed SI for pre-review that just has the essentials. The modeling details, all of
// the parameters and their provenance, and how all the figures were made in the MS" / "every
// equation, every parameter and its provenance should be in the SI for sure" / "it just needs to be
// so much shorter" / provenance as "Source, Page Number, Table".
// Built from the detailed SI's own elements: every equation and the section numbering are reused,
// prose is whole sentences selected from the detailed paragraphs (plus a few short linking sentences
// and captions written here), Table S7 carries every published parameter with a short locator from
// results/si_short_locators.json, and the reference list is renumbered by first appearance in the
// condensed document. data/check_si_condensed.py (G-SICOND) checks the result against the detailed SI.
// ================================================================================================
let DOC_FRONT = front, DOC_TABLES2 = tableS2, DOC_BACK = back;
if (SI_MODE === "condensed") {
  const SL = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "si_short_locators.json"), "utf8"));
  const ALL = [...front, ...tableS2, ...back];
  const one = (hits, label) => { if (hits.length !== 1) throw new Error("condensed plan: " + label + " matched " + hits.length + " elements"); return hits[0]; };
  const P = (pre) => one(ALL.filter(e => e.__kind === "p" && e.__t.startsWith(pre)), "paragraph «" + pre + "»");
  const C = (pre) => one(ALL.filter(e => e.__kind === "cap" && e.__t.startsWith(pre)), "caption «" + pre + "»");
  const EQ = (tag) => one(ALL.filter(e => e.__kind === "eq" && e.__t === "(" + tag + ")"), "equation " + tag);
  const H = (pre) => one(ALL.filter(e => e.__kind === "h" && e.__t.startsWith(pre)), "heading «" + pre + "»");
  const T = (pre, nth = 0) => { const hits = ALL.filter(e => e.__kind === "table" && e.__t.startsWith(pre)); if (!hits[nth]) throw new Error("condensed plan: table «" + pre + "» #" + nth); return hits[nth]; };
  const CELLS = (tb) => tb.__cells.split("\n").map(r => r.split(" | "));
  const pick = (text, pres, label) => pres.map(pre => one(splitSentences(text).filter(x => x.startsWith(pre)), label + " sentence «" + pre + "»")).join(" ");
  const KEEP = (pre, pres) => p(pick(P(pre).__t, pres, "«" + pre + "»"));
  const KEEPCAP = (pre, pres) => cap(pick(C(pre).__t, pres, "«" + pre + "»"));
  const refsIn = (s) => { const ks = []; (s.match(/«([^»]+)»|⟦([^⟧]+)⟧/g) || []).forEach(m => m.slice(1, -1).split(",").forEach(k => { k = k.trim(); if (!ks.includes(k)) ks.push(k); })); return ks; };
  const regLoc = (name) => { if (!(name in SL.registry)) throw new Error("condensed Table S7/S4: no short locator for '" + name + "'"); return SL.registry[name]; };

  // ---- front matter: title page, S1-S4 ----
  const titleEnd = front.indexOf(H("S1. "));
  const qStart = front.indexOf(P("**Stage 1, topic query.**")) + 1, qEnd = front.indexOf(P("The exclusions remove adjacent"));
  const s1Table = CELLS(T("Archetype"));
  const S1_SOURCE = [
    "derived (Wilke, Eisenberg & Tobias 1953, Eq. XVII)",
    "measured on a proxy system (Williams et al. 2019, p. 1228)",
    "measured (⟦watkins2023⟧, SI Table S1)",
    "measured (⟦watkins2023⟧, SI Table S1)",
    "derived (⟦mo2020⟧, SI p. 13)",
    "measured (⟦bard⟧, p. 30)",
    "measured (⟦eisenberg⟧, Eq. IX p. 312, Fig. 10 p. 314)"];
  if (s1Table.length !== S1_SOURCE.length) throw new Error("condensed Table S1: row count changed");
  const s4Table = CELLS(T("Electrolyte | κ"));
  const s2Rows = CELLS(tableS2[0]);
  if (s2Rows.length !== SL.table_s2.length) throw new Error("condensed Table S2: " + s2Rows.length + " rows against " + SL.table_s2.length + " locators");
  DOC_FRONT = [
    ...front.slice(0, titleEnd),
    H("S1. "),
    KEEP("We quantify the transport-limited", ["We quantify the transport-limited", "Stage 0 evaluates", "Stage 1 resolves", "A companion module", "The transport solvers are implemented"]),
    p("Stage 2 adds the homogeneous chemical step for the mediated and catalyst-carried entries (§S5.4 and §S5.7)."),
    H("S1.1 "),
    KEEP("Four modelling choices define", ["Four modelling choices define"]),
    KEEP("(i) The transport problem", ["(i) The transport problem", "This treatment is necessary"]),
    KEEP("(ii) The viscosity is the", ["(ii) The viscosity is the", "μ in Table S3 is the"]),
    KEEP("(iii) The model computes", ["(iii) The model computes", "There is no electrode kinetics", "Electrode kinetics are omitted"]),
    KEEP("(iv) The diffusion layer", ["(iv) The diffusion layer", "δ is a measured film"]),
    KEEP("The numerical implementation is verified", ["The numerical implementation is verified"]),
    H("S2. "),
    P("The limiting current density for a species that must reach"), EQ("S1"),
    KEEP("where D_c and C_c are", ["where D_c and C_c are", "We classify every reaction by its carrier"]),
    KEEP("δ is obtained per reactor archetype", ["δ is obtained per reactor archetype", "Where a correlation applies"]),
    mkTable(["Archetype", "Model", "Geometry / operating point", "Correlation", "Source"],
      s1Table.map((r, i) => [r[0], r[1], r[2], r[3], S1_SOURCE[i]]), [1400, 1350, 1900, 1900, 2170]),
    cap("Table S1. Reactor archetypes and the source of δ for each. δ is evaluated per species from its D and the solvent ν. Values and locators: Table S7g."),
    H("S3. "), H("S3.1 "),
    P("Direct measurements of diffusion coefficients"), EQ("S2"),
    KEEP("with solvent molar mass M_B", ["with solvent molar mass M_B"]),
    P("Three carrier types receive dedicated treatment."),
    KEEP("Supporting-electrolyte ions in solvents", ["Supporting-electrolyte ions in solvents", "Because a supporting ion carries no flux"]),
    H("S3.2 "),
    T("Solvent | M"),
    cap("Table S3. Solvent properties used in Eq. S2 and in ν = μ/ρ for the reactor correlations. Only the product φM enters Eq. S2, so for the mixtures the tabulated M and φ are a split of the Perkins–Geankoplis product (ref. ⟦poling⟧, Eq. 11-12.4, p. 618). Values, states and locators: Table S7b."),
    mkTable(["Electrolyte", "κ (mS/cm)", "State", "Source"],
      s4Table.map(r => [r[0], r[1], r[2], regLoc(r[0].replace(/ \/ /g, "/").replace(" (aq)", " aq"))]), [2200, 900, 1000, 5620]),
    cap("Table S4. Ionic conductivities (25 °C) used in the ohmic and thermal analysis of §S6. The derivation of the NaI/DMF value is given with Eq. S27; values, states and locators: Table S7f."),
    H("S3.3 "),
    KEEP("Table S1 gives each archetype its correlation", ["Eisenberg, Tobias and Wilke fit", "The fifty rows here run Sc", "The Reynolds number at this operating point"]),
    KEEP("We bound this extrapolation with a second", ["We bound this extrapolation with a second", "Jang and co-workers", "Eisenberg is retained as the primary"]),
    KEEP("The difference between the correlations", ["Per row the second correlation gives"]),
    H("S4. "), H("S4.1 "),
    KEEP("The dataset plotted in main-text Figure 1", ["The dataset plotted in main-text Figure 1"]),
    P("**Stage 1, topic query.**"), ...front.slice(qStart, qEnd),
    P("The exclusions remove adjacent"), P("**Stage 2, reaction filter.**"), P("**Deduplication.**"),
    P("**Atom mapping.**"), P("**Classification.**"), P("**Redox assignment.**"),
    P("**Scale and readiness.**"),
    H("S4.2 "),
    KEEP("The set is stratified by the reaction-class", ["The set is stratified by the reaction-class", "Two of the fifty rows fall outside", "Set share against dataset share", "On that basis the set is approximately"]),
    p("Every concentration, solvent and electrolyte in Table S2 is taken from the standard or scaled conditions of the named exemplar, except where stated below, and converted to molarity from the stated amounts and volumes; the locator for each row is given in Table S2."),
    KEEP("The set is stratified by the reaction-class", ["Forty-eight of the fifty rows are verified this way", "Two are not"]),
    cap("Table S2 (following pages, landscape). The 50-reaction set: carrier assignment, carrier charge z at the electrode, carrier diffusivity and its estimation method (§S3.1), concentration, electrons per carrier turnover n_c, solvent, electrolyte and source. " + pick(C("Table S2 (following pages").__t, [numWordCap(CC_MEDIUM.length) + " rows, marked *"], "Table S2 caption") + " The source column gives the exemplar reference and the page, table or figure of the conditions used."),
  ];
  DOC_TABLES2 = [
    mkTable(["#", "Class", "Reaction", "Carrier", "Carrier species", "z", "D (cm²/s)", "C (M)", "n_c", "Solvent", "Electrolyte", "D method", "Source"],
      s2Rows.map((r, i) => [...r.slice(0, 12), "[⟦" + ROWKEYS[i] + "⟧]" + (SL.table_s2[i] ? " " + SL.table_s2[i] : "")]),
      [400, 1000, 2600, 850, 1400, 350, 950, 650, 450, 950, 1600, 1450, 1390], 14040),
    H("S4.3 "), P("Table S10 writes out the chemistry"), C("Table S10. "), T("# | Reaction | Electrode"),
  ];

  // ---- back matter: S5-S11 ----
  const s6Rows = CELLS(T("Mediated system"));
  const catRowsC = CELLS(T("Catalyst-carried entry"));
  const catHdr = T("Catalyst-carried entry").__t.split(" | ");
  const s7Tabs = ALL.filter(e => e.__kind === "table" && e.__t.startsWith("Parameter | Value | Units | State"));
  const s7Caps = ALL.filter(e => e.__kind === "cap" && /^Table S7[a-k]\. /.test(e.__t));
  if (s7Tabs.length !== s7Caps.length) throw new Error("condensed Table S7: " + s7Tabs.length + " tables against " + s7Caps.length + " captions");
  const S7C = [];
  s7Tabs.forEach((tb, i) => {
    S7C.push(mkTable(["Parameter", "Value", "Units", "State", "Eq.", "Source"],
      CELLS(tb).map(r => [r[0], r[1], r[2], r[3], r[4], regLoc(r[0])]), [2300, 1000, 800, 900, 600, 4120]));
    S7C.push(cap(pick(s7Caps[i].__t, ["Table S7", s7Caps[i].__t.split(". ")[1].slice(0, 12)], "Table S7 caption")));
  });
  const sec11 = back.slice(back.indexOf(H("S11. ")), back.indexOf(H("References")));
  DOC_BACK = [
    H("S5. "), H("S5.1 "),
    P("Within the film 0 ≤ x ≤ δ we solve"), EQ("S3"), P("Conservation of mass for every species j"), EQ("S4"),
    P("where the single homogeneous step has"), EQ("S5"), P("with stoichiometric coefficients ν_ox"), EQ("S6"),
    P("Conservation of charge is not imposed separately"), EQ("S7"), P("so the current entering at the electrode"), EQ("S8"),
    KEEP("the first being the galvanostatic electrode condition", ["the first being the galvanostatic electrode condition"]),
    H("S5.2 "),
    P("The film is discretized in N finite volumes"), EQ("S9"), P("and the discrete statement of Eq. S4"), EQ("S10"),
    KEEP("with the electrode face flux replaced", ["with the electrode face flux replaced", "The unknowns are the logarithms", "The nonlinear system F(u) = 0"]),
    EQ("S11"), P("with a dense forward-difference Jacobian"),
    H("S5.3 "), P("Two analytic limits constrain the implementation."),
    H("S5.4 "),
    P("Treating a mediator as a species that merely commutes"), EQ("S12"), EQ("S13"), EQ("S14"), EQ("S15"),
    P("valid in the regimes δ/x_k"), EQ("S16"),
    KEEP("Both diffusivities in those two groups", ["The three rows drawn in main-text Fig. 6d–f"]),
    P("Because x_k shrinks to sub-micrometer scale"),
    KEEP("The solver reproduces the three analytic regimes.", ["The solver reproduces the three analytic regimes.", "As k → 0 the plateau recovers", "At intermediate k the computed plateau", "At larger k still, the system enters"]),
    H("S5.5 "),
    KEEP("Every mediated entry of the 50-reaction set", ["Every mediated entry of the 50-reaction set", "Electron bookkeeping:", "Every specification is checked at runtime", "Ramping the current cannot cross", "The ramp is therefore used only", "Of the " + CENSUS.nall + " mediated cells, " + CENSUS.n + " end on a plateau", "The " + numWord(PC.cells.length) + " cells above", WALL_SENT.slice(0, 24)]),   // pass 16: the census needs the ten floor cells too
    mkTable(["Mediated system", "k (M⁻¹s⁻¹)", "k source", "x_k (μm)", "stirred: Stage-0 → EC′ (mA/cm²)", "ANEC: Stage-0 → EC′", "limiter at i_lim", "EC′, unstirred → rotating cylinder (gain)"],
      s6Rows.map(r => [r[0], r[1], "⟦" + refsIn(r[2]).join(",") + "⟧", r[3], r[4], r[5], r[6], r[7]]), [1900, 700, 1100, 600, 1350, 1250, 1720, 1100]),
    KEEPCAP("Table S6.", ["Table S6.", "The mediated EC\u2032 matrix", "Fitting ln i_lim", "Stage-0 is the commuting bound", "The limiter is read from the seven solved cells"]),   // 2026-09-21: the main text cites Table S6 for the log-log slopes; the condensed caption had dropped that sentence
    // pass 15: the main text cites S5.5 for the tenfold rate-constant sweep, which the condensed build did not carry
    p((() => { const dm = Math.max(KS.summary.max_count_delta_25, KS.summary.max_count_delta_50);
      if (!KS.summary.ordering_preserved || dm > 1) throw new Error("condensed S5.5: the tenfold sweep moves a count by " + dm + " or changes an ordering");
      return "Perturbing each finite rate constant by a factor of ten in either direction, one row at a time, and re-solving the mediated matrix moves the ≥25 and ≥50 mA cm⁻² counts of any single architecture by at most " + numWord(dm) + " reaction and leaves the ordering the main text claims intact: unstirred below stirred below recirculating flow below the ANEC cell, with the three thin-film archetypes above it."; })()),
    P("The same content can be read nondimensionally"), EQ("S17"),
    KEEP("with μ = n_c C_med D_med", ["with μ = n_c C_med D_med"]),
    H("S5.6 "), P("Every continuum-model configuration with a tractable"),
    H("S5.7 "),
    KEEP("Mechanistically a molecular catalyst is an EC′ carrier", ["Mechanistically a molecular catalyst is an EC′ carrier", "Credited with no turnover inside the film", "The mediated rows each carry"]),
    KEEP("For " + numWord(SR.n_sourced) + " of the " + numWord(N_CAT) + " rows that step has been measured", ["For " + numWord(SR.n_sourced) + " of the " + numWord(N_CAT) + " rows that step has been measured", "Two nickel rows", "For the isolated Ni(I) complex", "The homocoupling solves bromobenzene", "The adopted value is 10²", "Two cobalt-hydride rows", "A voltammetric simulation of the Co(salen) hydride", "The remaining " + numWord(SR.n_floor) + " rows", "For three of them a finite constant", "In the two nickel aminations", "The Co(salen) allylic C–H amination regenerates"]),
    P("The three rows drawn in main-text Fig. 6h"),
    P("Sensitivity. All "), P("Result. "),    // pass 15: the main text cites S5.7 for the band the catalyst rows are re-solved over and what its top buys
    mkTable(catHdr.slice(0, 6), catRowsC.map(r => r.slice(0, 6)), [2.8, 0.8, 0.8, 2.5, 1.2, 1.6]),
    cap("Catalyst-carried entries: catalyst and substrate concentrations, the substrate each exemplar names with its Wilke–Chang diffusivity, the adopted rate constant (§S5.7, Table S7j) and the ceiling the matrix publishes at it (the largest of the seven architectures)."),
    P("Table S11 lists, for each of the"), T("Entry | Step solved"), C("Table S11. "),
    H("S6. "), P("The cell-voltage stack is"), EQ("S18"), P("with a representative E₀ = 2.0 V"), EQ("S19"),
    p("The main-text example, 0.1 M Bu₄NBF₄/DMF (κ = 4.76 mS cm⁻¹, Table S7f) across a 5 mm gap at 100 mA cm⁻², gives " + f2(EX_ECELL) + " V, of which " + f2(EX_OHMIC) + " V is ohmic, " + f2(EX_Q) + " W cm⁻² of heat and a passive steady state of " + EX_TSS.toFixed(0) + " °C in the 100 mL beaker of §S6.1. Across the 2 cm beaker gap of §S6.1, 0.2 M NaI/DMF (κ = " + NAI.k + " mS cm⁻¹, Table S4) draws " + DMFX.E_cell_50_V.toFixed(1) + " V at 50 mA cm⁻², most of it ohmic, and stays inside 10–20 V for κ between " + DMFX.kappa_E50_20V_mScm.toFixed(2) + " and " + DMFX.kappa_E50_10V_mScm.toFixed(2) + " mS cm⁻¹."),
    H("S6.1 "),
    p("We close a lumped energy balance on a representative 100 mL cell with 10 cm² electrodes. " + pick(P("To answer whether cells actually reach solvent boil-off").__t, ["The dissipated overpotential heat per electrode area"], "S6.1 opening")),
    EQ("S20"), EQ("S21"), EQ("S22"),
    KEEP("where U′ = UA/A_elec is the heat-rejection coefficient", ["where U′ = UA/A_elec", "The passive coefficient is derived", "Treating the internal and external films", "For the 100 mL beaker, σ is"]),
    p("For the compact cells σ is ≈7 for the microfluidic chip and ≈0.8 for an interior cell of a zero-gap stack; the recirculating flow cell and the two rotating electrodes take the beaker value, and each value is given in Table S7i."),
    p("Each preparative architecture is evaluated at its own median limiting current from Table S5; the zero-gap stack runs at its declared 1 A cm⁻², and the ANEC cell is not evaluated."),
    KEEP("This section separates the variables that decide whether a cell boils", ["Fixing the reactor", "At the two rotating archetypes", "The THF failures there hold", "In the unstirred, stirred and recirculating cells THF clears", "The zero-gap stack fails in all four", "The microfluidic cell clears all four"]),
    H("S6.2 "),
    p("Setting T_ss to the boiling point at each architecture's transport ceiling gives the required heat-rejection coefficient, U′_req = q(i_design)/(T_b − T_amb), which is compared with the liquid cooling of each cell's own construction (Table S7i) and with its passive coefficient. " + pick(P("Where a cell does fall short the design question").__t, ["Where passive rejection falls short", "Liquid cooling is built as each cell would be cooled", "Against those ranges"].concat(CF_COND_ACTIVE.length ? [numWordCap(CF_COND_ACTIVE.length) + " of these verdicts move"] : []).concat(["Only THF's duty at the rotating cylinder", "Table S12 sweeps"]), "S6.2")),
    ...S12_EL(),
    H("S6.3 "),
    KEEP("The analysis above uses the 25 °C conductivities", ["The analysis above uses the 25 °C conductivities", "Conductivity rises with temperature"]),
    p("We bracket the effect: the lower end is κ fixed at 25 °C, the value used throughout §S6; the upper end is Arrhenius scaling of κ from 25 °C to the boiling point with an activation energy of 15 kJ mol⁻¹ (Table S7i)."),
    KEEP("Applied at each solvent's boiling point", ["Applied at each solvent's boiling point", "The unstirred-beaker ceilings of §S6.1 then move"]),
    H("S6.4 "),
    KEEP("Two terms in the heat balance carry no source", ["Two terms in the heat balance carry no source", "Each is swept and reported as a breaking point"]),
    H("S7. "),
    KEEP("The full matrix applies the same physical model", ["The full matrix applies the same physical model", "All 350 cells are converged solutions"]),
    T("Reactor archetype | median"), KEEPCAP("Table S5.", ["Table S5.", "Results across the 50-reaction set"]),
    KEEP("These thresholds are anchored in the pharmaceutical-industry survey", ["These thresholds are anchored"]),
    H("S8. "),
    KEEP("The parameter table quantifies the data problem", ["The parameter table quantifies the data problem"]),
    p("The resulting bounds on the reported quantities are given in §S10 (Tables S8 and S9), and the extrapolation of the rotating-cylinder correlation in §S3.3."),
    H("S8.1 "),
    p("Productivity and pumping cost are computed for a pair of laminar parallel-plate channels, 1 mm / 5 cm / 5 cm s⁻¹ and 250 µm / 2.5 cm / 10 cm s⁻¹ (gap / length / mean velocity; Table S7g). " + pick(P("A limiting current density is a flux").__t, ["Residence time is τ = L/u", "At the median carrier diffusivity"], "S8.1")),
    KEEP("Comparing the 1 mm and 250 µm channels", ["The thinner gap lowers δ", "Although the residence time decreases", "The tradeoff is pumping"]),
    H("S9. "),
    KEEP("Table S7 groups every model parameter by category", ["Table S7 groups every model parameter", "Measured values are tied to", "Derived values are calculated"]),
    p("Assumed values are used only when no suitable source is available, and each carries a sensitivity range and the conclusion it affects; this condensed version of Table S7 omits those columns, which the full Supporting Information, available from the authors, prints."),
    H("S9.0 "),
    KEEP("Each row of Table S7 carries an Equation column", ["Each row of Table S7 carries an Equation column"]),
    EQ("S23"), KEEP("Le Bas additive molar volume", ["Le Bas additive molar volume", "Increments v_i and the ring corrections"]),
    EQ("S24"), KEEP("Stokes–Einstein, used for the", ["Stokes–Einstein, used for the"]),
    EQ("S25"), P("Nernst–Einstein, used for the " + numWord(N_NE) + " small-ion carriers"),
    EQ("S26"), P("Casteel–Amis."),
    EQ("S27"), EQ("S28"), KEEP("Kohlrausch additivity and the ceiling it implies.", ["Kohlrausch additivity and the ceiling it implies."]),
    EQ("S29"), KEEP("The Debye–Hückel–Onsager limiting law", ["The Debye–Hückel–Onsager limiting law"]),
    EQ("S30"), P("Perkins–Geankoplis mole-fraction rule"), EQ("S31"), P("Kinematic viscosity, which enters the Schmidt number"),
    EQ("S32"), EQ("S33"), KEEP("Surrogate-anchored diffusivity", ["Surrogate-anchored diffusivity", "Eq. S32 is Eq. S2 written for two solutes"]),
    ...S7C,
    H("S10. "),
    KEEP("Each quantity reported in the main text is given below", ["Each quantity reported in the main text is given below", "The model is re-evaluated at those limits"]),
    T("Reported quantity", 0), KEEPCAP("Table S8.", ["Table S8.", "Bounds on the transport quantities", "Medians in mA cm"]),
    T("Reported quantity", 1), KEEPCAP("Table S9.", ["Table S9.", "Bounds on the thermal quantities", "Ceilings and zero-gap currents", "Rows marked one-sided"]),
    ...sec11,
  ];

  // ---- references: renumbered by first appearance in the condensed document ----
  const order = [];
  [...DOC_FRONT, ...DOC_TABLES2, ...DOC_BACK].forEach(el => [el.__t, el.__cells].forEach(s => { if (s) refsIn(s).forEach(k => { if (!order.includes(k)) order.push(k); }); }));
  const REFKEYS = REFS.map(r => r.k);
  order.forEach(k => { if (!REFKEYS.includes(k)) throw new Error("condensed SI cites unknown reference " + k); });
  if (!process.env.SI_REFORDER) {
    const tmp = path.join(require("os").tmpdir(), "si_condensed_reforder_" + process.pid + ".json");
    fs.writeFileSync(tmp, JSON.stringify(order));
    require("child_process").execFileSync(process.execPath, [__filename], { env: { ...process.env, SI_REFORDER: tmp }, stdio: "inherit" });
    fs.unlinkSync(tmp);
    process.exit(0);
  }
  const want = JSON.parse(fs.readFileSync(process.env.SI_REFORDER, "utf8"));
  if (JSON.stringify(want) !== JSON.stringify(order))
    throw new Error("condensed SI: first-appearance order changed between passes");
  DOC_BACK.push(h1("References"),
    ...order.map((k, i) => new Paragraph({
      children: [new TextRun({ text: (i + 1) + "  ", size: 18, font: "Calibri" }),
                 ...REFS.find(r => r.k === k).s.map(sg => new TextRun({ text: sg.t, size: 18, font: "Calibri", italics: !!sg.i, bold: !!sg.b }))],
      spacing: { after: 40 }, indent: { left: 420, hanging: 420 } })));
  console.log("condensed SI: " + order.length + " of " + REFS.length + " references cited, renumbered by first appearance; "
    + (DOC_FRONT.length + DOC_TABLES2.length + DOC_BACK.length) + " elements");
}

const doc = new Document({
  styles: { default: { document: { run: { font: "Calibri", size: 20 } } } },
  sections: [
    { properties: { page: { ...letter, margin: { top: 1080, bottom: 1080, left: 1260, right: 1260 } } }, children: DOC_FRONT },
    { properties: { page: { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE }, margin: { top: 720, bottom: 720, left: 900, right: 900 } } }, children: DOC_TABLES2 },
    { properties: { page: { ...letter, margin: { top: 1080, bottom: 1080, left: 1260, right: 1260 } } }, children: DOC_BACK },
  ],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(OUT_DOCX, b);
  console.log("docx written -> " + OUT_DOCX);
  if (TABLE_DRIFT.length) {
  console.log("TABLE DRIFT corrected from the CSVs (" + TABLE_DRIFT.length + "):");
  TABLE_DRIFT.forEach(d => console.log("   " + d));
} else { console.log("Tables S3/S4: every typed number already matched the registry"); }
console.log("registry census: " + CENSUS_ALL.n + " parameters (" + CENSUS_ALL.measured + " measured, " +
              CENSUS_ALL.derived + " derived, " + CENSUS_ALL.assumption + " assumption); conductivities " +
              CENSUS_COND.n + " (" + CENSUS_COND.measured + "/" + CENSUS_COND.derived + "/" +
              CENSUS_COND.assumption + "), solver diffusivities " + CENSUS_DIFF.n +
              " (" + CENSUS_DIFF.assumption + " assumption)");
});
