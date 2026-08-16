import { useState } from "react";

interface Props {
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export function PredictionChallenge({ question, options, correctIndex, explanation }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const [revealed, setRevealed] = useState(false);

  function choose(idx: number) {
    if (revealed) return;
    setSelected(idx);
  }

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg p-4">
      <p className="text-sm text-slate-200 mb-3">{question}</p>
      <div className="space-y-2 mb-3">
        {options.map((opt, idx) => {
          const isCorrect = revealed && idx === correctIndex;
          const isWrongPick = revealed && selected === idx && idx !== correctIndex;
          return (
            <button
              key={idx}
              onClick={() => choose(idx)}
              className={`w-full text-left text-sm rounded-lg py-2 px-3 border transition-colors ${
                isCorrect
                  ? "bg-emerald-500/15 border-emerald-500 text-emerald-300"
                  : isWrongPick
                  ? "bg-rose-500/10 border-rose-500 text-rose-300"
                  : selected === idx
                  ? "bg-slate-800 border-slate-600 text-slate-100"
                  : "bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700"
              }`}
            >
              {opt}
            </button>
          );
        })}
      </div>
      {!revealed ? (
        <button
          onClick={() => setRevealed(true)}
          disabled={selected === null}
          className="text-sm text-emerald-400 hover:text-emerald-300 disabled:opacity-40 disabled:hover:text-emerald-400"
        >
          Reveal answer
        </button>
      ) : (
        <p className="text-xs text-slate-400 leading-snug border-t border-slate-800 pt-2">
          {selected === correctIndex ? "Correct. " : "Not quite. "}
          {explanation}
        </p>
      )}
    </div>
  );
}
