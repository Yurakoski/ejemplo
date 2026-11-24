import random
import tkinter as tk
from typing import List, Optional


Board = List[Optional[str]]

BG = "#0B1120"
PANEL = "#121C2F"
PANEL_LIGHT = "#1A2740"
CELL = "#17243A"
CELL_HOVER = "#21324D"
CELL_SHADOW = "#050A13"
TEXT = "#F2F6FC"
MUTED = "#91A0B8"
ACCENT = "#5DE0C0"
PLAYER_COLOR = "#72A7FF"
COMPUTER_COLOR = "#FF8D9A"

WINNING_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def find_winner(board: Board) -> Optional[str]:
    for first, second, third in WINNING_LINES:
        mark = board[first]
        if mark is not None and mark == board[second] == board[third]:
            return mark
    return None


def choose_computer_move(board: Board) -> int:
    """Prefer a draw, but sometimes choose a move that can change the outcome."""

    def minimax(position: Board, is_computer_turn: bool, depth: int) -> int:
        winner = find_winner(position)
        if winner == "O":
            return 10 - depth
        if winner == "X":
            return depth - 10
        if all(mark is not None for mark in position):
            return 0

        scores = []
        mark = "O" if is_computer_turn else "X"
        for index, cell in enumerate(position):
            if cell is None:
                position[index] = mark
                scores.append(minimax(position, not is_computer_turn, depth + 1))
                position[index] = None
        return max(scores) if is_computer_turn else min(scores)

    move_scores = []
    for index, cell in enumerate(board):
        if cell is None:
            board[index] = "O"
            score = minimax(board, False, 1)
            board[index] = None
            move_scores.append((index, score))
    if not move_scores:
        raise ValueError("No hay movimientos disponibles.")

    best_score = max(score for _, score in move_scores)
    draw_moves = [index for index, score in move_scores if score == 0]
    if draw_moves:
        return random.choice(draw_moves)

    fallback_score = (
        min(score for _, score in move_scores) if best_score > 0 else best_score
    )
    fallback_moves = [
        index for index, score in move_scores if score == fallback_score
    ]
    return random.choice(fallback_moves)


class TicTacToeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Ta Te Ti | Duelo")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.window_width = min(560, screen_width - 32)
        self.window_height = min(760, screen_height - 72)
        self.compact = self.window_height < 740
        self.page_padding = 22 if self.window_width >= 460 else 12
        self.cell_size = max(
            58,
            min(
                138,
                (self.window_width - 2 * self.page_padding - 28) // 3,
                (self.window_height - (330 if self.compact else 340)) // 3,
            ),
        )
        self.root.minsize(self.window_width, self.window_height)
        self.root.geometry("{}x{}".format(self.window_width, self.window_height))

        self.board: Board = [None] * 9
        self.round_over = False
        self.ai_pending = False
        self.ai_job: Optional[str] = None
        self.score = {"X": 0, "O": 0, "draw": 0}
        self.cells: List[tk.Button] = []

        self._build_interface()
        self._center_window()
        self._update_score()

    def _center_window(self) -> None:
        self.root.update_idletasks()
        width = self.window_width
        height = self.window_height
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry("{}x{}+{}+{}".format(width, height, x, y))

    def _build_interface(self) -> None:
        page = tk.Frame(
            self.root,
            bg=BG,
            padx=self.page_padding,
            pady=12 if self.compact else 18,
        )
        page.pack(fill="both", expand=True)

        brand = tk.Frame(page, bg=BG)
        brand.pack(fill="x")
        tk.Label(
            brand,
            text="JUEGO RÁPIDO  /  01",
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT,
            bg=BG,
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="Ta Te Ti",
            font=("Segoe UI", 26 if self.compact else 29, "bold"),
            fg=TEXT,
            bg=BG,
        ).pack(anchor="w", pady=(5, 0))
        tk.Label(
            brand,
            text="Un clásico. Un rival que no se distrae.",
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=BG,
        ).pack(anchor="w", pady=(1, 0))

        self.status_card = tk.Frame(
            page,
            bg=PANEL,
            padx=12,
            pady=8 if self.compact else 11,
        )
        self.status_card.pack(fill="x", pady=(10, 8) if self.compact else (18, 12))
        self.status_dot = tk.Label(
            self.status_card,
            text="●",
            font=("Segoe UI", 11),
            fg=PLAYER_COLOR,
            bg=PANEL,
        )
        self.status_dot.pack(side="left", padx=(0, 10))
        self.status_label = tk.Label(
            self.status_card,
            text="Tu turno: elige una casilla",
            font=("Segoe UI", 11, "bold"),
            fg=TEXT,
            bg=PANEL,
        )
        self.status_label.pack(side="left")
        tk.Label(
            self.status_card,
            text="TÚ  X",
            font=("Segoe UI", 9, "bold"),
            fg=PLAYER_COLOR,
            bg=PANEL,
        ).pack(side="right")

        cell_gap = 8
        board_frame = tk.Frame(
            page,
            bg=BG,
            width=3 * self.cell_size + 2 * cell_gap,
            height=3 * self.cell_size + 2 * cell_gap,
        )
        board_frame.pack()
        board_frame.pack_propagate(False)
        for index in range(9):
            row, column = divmod(index, 3)
            x = column * (self.cell_size + cell_gap)
            y = row * (self.cell_size + cell_gap)
            face_size = self.cell_size - 6
            tk.Frame(board_frame, bg=CELL_SHADOW, bd=0).place(
                x=x + 6,
                y=y + 6,
                width=face_size,
                height=face_size,
            )
            cell = tk.Button(
                board_frame,
                text="",
                font=("Segoe UI", 30 if self.cell_size >= 90 else 23, "bold"),
                fg=TEXT,
                bg=CELL,
                activeforeground=TEXT,
                activebackground=CELL_HOVER,
                disabledforeground=TEXT,
                relief="raised",
                overrelief="raised",
                bd=3,
                highlightthickness=0,
                width=1,
                height=1,
                cursor="hand2",
                command=lambda cell_index=index: self._play(cell_index),
            )
            cell.place(
                x=x,
                y=y,
                width=face_size,
                height=face_size,
            )
            cell.bind("<Enter>", lambda event, button=cell: self._on_hover(button, True))
            cell.bind("<Leave>", lambda event, button=cell: self._on_hover(button, False))
            self.cells.append(cell)

        score_card = tk.Frame(page, bg=PANEL, padx=8, pady=8 if self.compact else 11)
        score_card.pack(fill="x", pady=(10, 0) if self.compact else (14, 0))
        self.player_score = self._score_column(score_card, "TUS VICTORIAS", PLAYER_COLOR)
        self.draw_score = self._score_column(score_card, "EMPATES", MUTED)
        self.computer_score = self._score_column(score_card, "VICTORIAS PC", COMPUTER_COLOR)
        self.player_score.pack(side="left", expand=True, fill="x")
        self.draw_score.pack(side="left", expand=True, fill="x")
        self.computer_score.pack(side="left", expand=True, fill="x")

        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="x", pady=(10, 0) if self.compact else (14, 0))
        tk.Button(
            actions,
            text="↻   Jugar otra vez",
            font=("Segoe UI", 10, "bold"),
            fg=BG,
            bg=ACCENT,
            activeforeground=BG,
            activebackground="#7BE9D0",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._new_round,
            padx=14,
            pady=8 if self.compact else 10,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Button(
            actions,
            text="Reiniciar marcador",
            font=("Segoe UI", 9),
            fg=MUTED,
            bg=PANEL,
            activeforeground=TEXT,
            activebackground=PANEL_LIGHT,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._reset_score,
            padx=10,
            pady=8 if self.compact else 10,
        ).pack(side="left", padx=(6, 0))

        tk.Label(
            page,
            text="JUGADOR  X     ·     PC  O     ·     MEJOR DE TRES… O LAS QUE QUIERAS",
            font=("Segoe UI", 8, "bold"),
            fg="#64748B",
            bg=BG,
        ).pack(pady=(8, 0) if self.compact else (12, 0))

    def _score_column(self, parent: tk.Frame, title: str, color: str) -> tk.Frame:
        column = tk.Frame(parent, bg=PANEL)
        tk.Label(
            column,
            text=title,
            font=("Segoe UI", 8, "bold"),
            fg=MUTED,
            bg=PANEL,
        ).pack()
        value = tk.Label(
            column,
            text="0",
            font=("Segoe UI", 20, "bold"),
            fg=color,
            bg=PANEL,
        )
        value.pack(pady=(3, 0))
        column.value_label = value
        return column

    def _on_hover(self, button: tk.Button, entering: bool) -> None:
        if str(button["state"]) == "disabled" or button["text"]:
            return
        button.configure(bg=CELL_HOVER if entering else CELL)

    def _play(self, index: int) -> None:
        if self.round_over or self.ai_pending or self.board[index] is not None:
            return

        self._place_mark(index, "X")
        if self._finish_if_needed():
            return

        self.ai_pending = True
        self.status_label.configure(text="La PC está pensando…")
        self.status_dot.configure(fg=COMPUTER_COLOR)
        self.ai_job = self.root.after(350, self._computer_turn)

    def _computer_turn(self) -> None:
        self.ai_job = None
        self.ai_pending = False
        if self.round_over:
            return
        self._place_mark(choose_computer_move(self.board), "O")
        if not self._finish_if_needed():
            self.status_label.configure(text="Tu turno: elige una casilla")
            self.status_dot.configure(fg=PLAYER_COLOR)

    def _place_mark(self, index: int, mark: str) -> None:
        self.board[index] = mark
        button = self.cells[index]
        button.configure(
            text=mark,
            fg=PLAYER_COLOR if mark == "X" else COMPUTER_COLOR,
            bg=PANEL_LIGHT,
            relief="sunken",
            state="disabled",
            cursor="arrow",
        )

    def _finish_if_needed(self) -> bool:
        winner = find_winner(self.board)
        if winner == "X":
            self.score["X"] += 1
            self._finish_round("¡Ganaste esta partida!", PLAYER_COLOR, "X")
        elif winner == "O":
            self.score["O"] += 1
            self._finish_round("La PC se lleva esta ronda", COMPUTER_COLOR, "O")
        elif all(mark is not None for mark in self.board):
            self.score["draw"] += 1
            self._finish_round("Empate. ¡Bien jugado!", ACCENT, None)
        else:
            return False
        self._update_score()
        return True

    def _finish_round(self, message: str, color: str, winner: Optional[str]) -> None:
        self.round_over = True
        self.status_label.configure(text=message)
        self.status_dot.configure(fg=color)
        for button in self.cells:
            if not button["text"]:
                button.configure(state="disabled", cursor="arrow")
        if winner is not None:
            for first, second, third in WINNING_LINES:
                if self.board[first] == self.board[second] == self.board[third] == winner:
                    for index in (first, second, third):
                        self.cells[index].configure(bg="#263953")

    def _update_score(self) -> None:
        self.player_score.value_label.configure(text=str(self.score["X"]))
        self.computer_score.value_label.configure(text=str(self.score["O"]))
        self.draw_score.value_label.configure(text=str(self.score["draw"]))

    def _new_round(self) -> None:
        if self.ai_job is not None:
            self.root.after_cancel(self.ai_job)
            self.ai_job = None
        self.board = [None] * 9
        self.round_over = False
        self.ai_pending = False
        for button in self.cells:
            button.configure(
                text="",
                fg=TEXT,
                bg=CELL,
                relief="raised",
                state="normal",
                cursor="hand2",
            )
        self.status_label.configure(text="Tu turno: elige una casilla")
        self.status_dot.configure(fg=PLAYER_COLOR)

    def _reset_score(self) -> None:
        self.score = {"X": 0, "O": 0, "draw": 0}
        self._update_score()
        self._new_round()


def main() -> None:
    root = tk.Tk()
    TicTacToeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()