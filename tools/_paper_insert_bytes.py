"""Insert the byte-axis subsection, the abstract sentence and the limitation into main.tex.

Every replacement is anchored on an exact existing string so a second run is a no-op and a
mismatch fails loudly instead of silently editing the wrong place.
"""
import io
import sys

P = r"D:\3dsg_1\submission\cviu\main.tex"

ABSTRACT_ANCHOR = (
    "cost at most $3.3$ points and\n"
    "nothing; the deletion criterion matters as much as the budget.")
ABSTRACT_NEW = (
    "cost at most $3.3$ points and\n"
    "nothing; the deletion criterion matters as much as the budget. Measured in bytes rather than\n"
    "in primitives the reading sharpens: deleting $70\\%$ of the primitives shrinks an asset only\n"
    "$3.7$--$3.9\\times$, and at that same byte budget a quantisation ladder reaches the same\n"
    "coverage to within $0.04$--$1.17$ points, so geometric editing is the least efficient way to\n"
    "spend a budget rather than merely a damaging edit.")

SECTION_ANCHOR = "\\subsection{Dose--response and granularity}\n\\label{sec:dose}"

SECTION = r"""\subsection{The ranking survives, the magnitude does not: the same edits at equal bytes}
\label{sec:bytes}

Every comparison so far holds the primitive count fixed. A compression claim, however, is about
bytes, and the two are not the same quantity: deleting $70\%$ of the primitives removes three
quarters of the carriers but keeps the remaining view-dependent coefficients at full width, so the
measured size of a ``prune to $30\%$'' asset falls only $3.66$--$3.90\times$
(Table~\ref{tab:bytes}, column \emph{prune 30\%}), while 8-bit quantisation of the same
coefficients alone is already $2.6$--$3.7\times$ and costs $0.0$ coverage points
(Table~\ref{tab:fidelity}). Sizes here are measured, not modelled: geometry and coefficients are
bit-packed plane by plane, ordered by the Morton code of the reconstructed means, and compressed
with \texttt{zstd} at level 12; the decoder rebuilds the means first and therefore needs no side
information to invert the order.

Once the budget is expressed in bytes, the edit that looks most benign becomes the most expensive.
Table~\ref{tab:bytes_vs} sets each asset's budget to the size its own prune-to-$30\%$ version
actually occupies, and asks what the least damaging non-deleting variant achieves for the same
number of bytes: a change of $-0.04$ to $-1.17$ points on all eight checkpoints, against $-7.1$ to
$-19.2$ points for the deletion, with PSNR flat or slightly improved. The ranking of edits is
therefore not reversed --- a point of coverage lost is still lost --- but the magnitude claim
collapses: deleting is the least efficient way to spend a byte budget, not the most damaging edit
per se. Table~\ref{tab:bytes} traces the whole frontier: the loss is $-0.39$ points at a $3\times$
budget and $0.00$ at $7\times$, and it does not improve further out to $24\times$, so the budget
that matters is the one below about $7\times$ and the paper's own operating point sits inside it.

\begin{table}[t]
\centering
\scriptsize
\caption{The same edits at equal bytes. Each cell is the least damaging \emph{measured} variant
that fits the column's budget, written as coverage change (points) / measured size
($\times$ reduction against the fp32 checkpoint) and the variant that achieves it:
\texttt{SH}$n$ is $n$-bit view-dependent coefficients, \texttt{+g8} also quantises the geometry
scalars to 8 bits, \texttt{+pos}$n$ stores positions relative to a Morton-ordered cluster, and
\texttt{MSC} selects a coding mode per primitive. No value is interpolated or extrapolated; the
$2\times$ column falls back to pruning because the ladder has no measured point below $2.1\times$.}
\label{tab:bytes}
\input{tab_frontier}
\end{table}

\begin{table}[t]
\centering
\scriptsize
\caption{Equal bytes, head to head. The budget of each row is the measured size of that asset's own
``prune to $30\%$'' version, and the fourth column is the least damaging non-deleting variant that
fits inside it. Coverage changes are paired drops over 400 splits; $\Delta$ is in coverage points.}
\label{tab:bytes_vs}
\input{tab_frontier_vs_prune}
\end{table}

The frontier is a property of the ladder we built, not a bound. We did not retrain, so an encoder
that re-optimises after quantisation would move it; we measure one archive at a quarter of the
captured resolution; and the treehill rows inherit the exposure mismatch of
section~\ref{sec:fidelity}, so their PSNR is reported but not interpreted. What the tables do
support is the narrower statement this paper needs: the coverage cost of a geometric edit is not an
intrinsic price of compression, and an audited asset can be shipped three to four times smaller
without measurable coverage loss.

"""

LIMIT_ANCHOR = "\\paragraph{What is not measured.}"
LIMIT_NEW = (
    "\\paragraph{Byte budgets are measured, not modelled.} The byte figures in\n"
    "section~\\ref{sec:bytes} come from one codec (bit-packed planes, Morton order, \\texttt{zstd}\n"
    "level 12) on one archive. A learned entropy model would move the absolute sizes and could move\n"
    "the ranking of variants within $5\\%$; the frontier is therefore reported with the codec\n"
    "stated, and no claim is made that it is the best achievable at a given size.\n"
    "\\paragraph{What is not measured.}")

first, second, third = (ABSTRACT_ANCHOR, SECTION_ANCHOR, LIMIT_ANCHOR)
s = io.open(P, encoding="utf-8").read()
if "\\label{sec:bytes}" in s:
    print("already inserted")
    sys.exit(0)
for anchor in (first, second, third):
    if s.count(anchor) != 1:
        raise SystemExit(f"anchor not unique ({s.count(anchor)}): {anchor[:60]!r}")
s = s.replace(first, ABSTRACT_NEW, 1)
s = s.replace(second, SECTION + second, 1)
s = s.replace(third, LIMIT_NEW, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("inserted abstract sentence, section sec:bytes and a limitation paragraph")
