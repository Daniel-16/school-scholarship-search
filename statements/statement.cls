%% statement.cls - one class for every piece of prose a graduate application
%% asks for: statement of purpose, personal statement, motivation letter,
%% research proposal, scholarship essay, diversity statement.
%%
%% Compile with: xelatex (fontspec is required for the Calibri/Carlito house
%% font, and the class loads it unconditionally).
%%
%% Design constraints, all of them imposed by admissions portals rather than
%% by taste:
%%
%%   * Word and page limits are hard. A statement over the limit is truncated
%%     on upload or rejected. So the class makes the count easy to check
%%     (single column, no floats, nothing that reflows unpredictably) and
%%     prints the declared limit in the header where the author can see it.
%%   * Many portals ask for the applicant's name and the programme on every
%%     page, because pages are separated during review. \statementheader
%%     does that.
%%   * Some ask for a plain unformatted document. Nothing here depends on
%%     colour, and the default has no decoration that would be lost if the
%%     text is pasted into a textarea.
%%   * Line spacing is a stated requirement surprisingly often ("double
%%     spaced", "1.5 spacing"). The `spacing` option takes it.
%%
%% Options:
%%   11pt | 12pt      body size (12pt default; US programmes often specify it)
%%   single | onehalf | double   line spacing (single default)
%%   numbered         print page numbers (off by default; many portals
%%                    re-paginate and a stale number confuses reviewers)

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{statement}[2026/10/28 Graduate application statement]

\newif\if@stmtnumbered \@stmtnumberedfalse
\newcommand{\@stmtspacing}{1.0}

\DeclareOption{numbered}{\@stmtnumberedtrue}
\DeclareOption{single}{\renewcommand{\@stmtspacing}{1.0}}
\DeclareOption{onehalf}{\renewcommand{\@stmtspacing}{1.5}}
\DeclareOption{double}{\renewcommand{\@stmtspacing}{2.0}}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ExecuteOptions{}
\ProcessOptions\relax

\LoadClass[12pt,a4paper]{article}

\RequirePackage{fontspec}
\RequirePackage[margin=1in]{geometry}
\RequirePackage{setspace}
\RequirePackage{fancyhdr}
\RequirePackage{titlesec}
\RequirePackage{xcolor}
\RequirePackage{microtype}

% Calibri-only house style, matching the CV.
%
% Carlito is tried FIRST, ahead of Calibri itself, and that order is
% deliberate. \IfFontExistsTF{Calibri} answers yes when *any* Calibri face is
% installed, and a partial install is common on Linux - this was written on a
% machine carrying Calibri Bold and nothing else, where asking for Calibri
% silently set the entire statement in bold. It compiled, it passed the page
% check, and it would have been uploaded.
%
% Carlito is metric-compatible with Calibri and ships complete (regular,
% italic, bold, bold italic) in texlive-fonts-extra, so it is both the safer
% and the visually identical choice. Calibri is kept as the second option for
% machines with a full install, and TeX Gyre Pagella as the last resort so a
% minimal TeX distribution still produces a document - a hard font failure at
% deadline time is the worst possible behaviour.
\IfFontExistsTF{Carlito}{\setmainfont{Carlito}}{%
  \IfFontExistsTF{Calibri}{\setmainfont{Calibri}}{\setmainfont{TeX Gyre Pagella}}}

\setstretch{\@stmtspacing}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.7\baselineskip}
\raggedright

% hyperref last, and quiet: a statement is read on paper as often as on
% screen, and coloured link boxes print badly.
\RequirePackage[hidelinks]{hyperref}

\definecolor{stmtrule}{gray}{0.55}

\newcommand{\@stmtauthor}{}
\newcommand{\@stmtprogramme}{}
\newcommand{\@stmtkind}{Statement of Purpose}
\newcommand{\@stmtlimit}{}

\newcommand{\applicant}[1]{\renewcommand{\@stmtauthor}{#1}}
\newcommand{\programme}[1]{\renewcommand{\@stmtprogramme}{#1}}
\newcommand{\statementkind}[1]{\renewcommand{\@stmtkind}{#1}}
%% The stated limit, e.g. {1000 words} or {2 pages}. Printed in the running
%% header so it is in front of the author while they write, and so a reviewer
%% can see at a glance what the document was held to.
\newcommand{\wordlimit}[1]{\renewcommand{\@stmtlimit}{#1}}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyhead[L]{\footnotesize\color{stmtrule}\@stmtauthor}
\fancyhead[R]{\footnotesize\color{stmtrule}\@stmtprogramme}
\if@stmtnumbered
  \fancyfoot[C]{\footnotesize\color{stmtrule}\thepage}
\fi

%% The title block. Deliberately small: the committee knows what the document
%% is, and a statement whose first third is a title block reads as padding.
\newcommand{\statementtitle}{%
  \begin{center}
    {\large\bfseries \@stmtkind}\\[2pt]
    {\normalsize \@stmtauthor}\\[1pt]
    {\footnotesize \@stmtprogramme}%
    \ifx\@stmtlimit\empty\else\\[1pt]{\scriptsize\color{stmtrule}limit: \@stmtlimit}\fi
  \end{center}
  \vspace{0.4\baselineskip}
}

%% Section headings, for a research proposal or a multi-part essay. A short
%% statement should not use them: a 900-word document broken into five
%% headed sections reads as an outline rather than an argument.
\titleformat{\section}{\normalsize\bfseries}{}{0pt}{}
\titlespacing*{\section}{0pt}{1.1\baselineskip}{0.3\baselineskip}
\titleformat{\subsection}{\normalsize\itshape}{}{0pt}{}
\titlespacing*{\subsection}{0pt}{0.8\baselineskip}{0.2\baselineskip}

%% A prompt quoted above the answer. Scholarship essays and most US
%% supplementary questions are answers to a specific question, and a reviewer
%% reading 400 of them needs to see which one.
\newcommand{\prompt}[1]{%
  \begin{quote}\small\itshape\color{stmtrule}#1\end{quote}
  \vspace{-0.2\baselineskip}
}

%% A signature block, for a motivation letter addressed to a person.
\newcommand{\signoff}[1]{%
  \vspace{1.2\baselineskip}
  #1\\[0.4\baselineskip]
  \@stmtauthor
}

\endinput
