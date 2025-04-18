#! /usr/bin/env python3
# encoding: UTF-8

# This file is part of SaGiDS.

# SaGiDS is free software: You can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.

# SaGiDS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the
# GNU General Public License along with SaGiDS.
# If not, see <https://www.gnu.org/licenses/>.


from collections import namedtuple
import dataclasses
from decimal import Decimal
from fractions import Fraction
import itertools
import logging
import pprint
import random
import sys
import turtle


class Grid:

    Option = namedtuple("Option", ["marker", "cell", "result", "transit", "total"], defaults=[None, None])

    @dataclasses.dataclass(frozen=True)
    class Cell:
        spot: turtle.Vec2D

        @property
        def value(self) -> int:
            return {
                0: {0: 1, 1: 7},
                1: {0: 3, 1: 5},
            }[int(self.spot[0]) % 2][int(self.spot[1]) % 2]

        def transits(self, cell: "Cell") -> bool:
            vector = cell.spot - self.spot
            return abs(vector[0]) == abs(vector[1])

    @dataclasses.dataclass
    class Marker:
        id: int
        value: Fraction = None
        grid: "Grid" = None
        cell: "Cell" = None

        @property
        def zone(self):
            try:
                quadrant = tuple(i // 2 for i in self.cell.spot)
                return [spot for spot in self.grid.cells if tuple(i // 2 for i in spot) == quadrant]
            except AttributeError:
                return []

        def results(self, cardinal: int):
            for n, d in zip(range(0, cardinal + 1), range(cardinal, -1, -1)):
                try:
                    yield Fraction(
                        (self.value.numerator + n) % 10,
                        (self.value.denominator + d) % 10,
                    )
                except ZeroDivisionError:
                    pass

        def options(self, cell: "Cell"):
            transits = [m for m in self.grid.markers.values() if m is not self and m.cell.transits(cell)]
            for r in self.results(cell.value):
                yield self.grid.Option(self, cell, r)
                for t in transits:
                    val = r * t.value
                    yield self.grid.Option(self, cell, r, t, val)

    @classmethod
    def build_markers(cls, k=4):
        return [
            cls.Marker(id=n+1, value=v)
            for n, v in enumerate(random.sample(
                [Fraction(n, 9) for n in [1, 2, 4, 5, 7, 8]],
                k
            ))
        ]

    @classmethod
    def build(cls, n_sectors=4, n_regions=4):
        rv = cls(markers=cls.build_markers(k=n_sectors))
        size = int(Decimal(n_sectors).sqrt() * Decimal(n_regions).sqrt())
        rv.cells = {
            pos: cls.Cell(turtle.Vec2D(*pos))
            for pos in itertools.product(range(size), repeat=2)
        }
        return rv

    def __init__(self, markers: list = None, cells: dict = None):
        self.markers = {i.id: i for i in markers}
        for mark in self.markers.values():
            mark.grid = self

        self.cells = cells or dict()

    def partition(self) -> list["Cell"]:
        markers = []
        pool = set(self.cells.values())
        while len(markers) < len(self.markers):
            cell = random.choice(list(pool))
            if not any(cell in m.zone for m in markers):
                m = self.Marker(len(markers), grid=self, cell=cell)
                if not any(m.cell.transits(i.cell) for i in markers):
                    markers.append(m)
                    zone = [self.Cell(spot=spot) for spot in m.zone]
                    pool = pool - set(zone)
        return [m.cell for m in markers]

    def mark(self, *args: tuple["Cell"]):
        for cell, marker in zip(args, self.markers.values()):
            marker.cell = self.cells[cell.spot]
        return self


def game(grid, limit=sys.maxsize, goal = Fraction(3, 16)):
    logger = logging.getLogger()

    moves = []
    n = 0
    while n < limit:
        for marker in grid.markers.values():
            options = list()
            for spot in marker.zone:
                cell = grid.cells[spot]
                if cell == marker.cell:
                    continue

                options.extend(marker.options(cell))

            chosen = next((i for i in options if i.total == goal), random.choice(options))
            logger.info(f"Player {marker.id} moves to {cell.spot}. Takes value {chosen.result}.")
            marker.cell = chosen.cell
            marker.value = chosen.result
            moves.append(chosen)
            if chosen.total == goal:
                logger.info(
                    f"Player {marker.id} wins against player {chosen.transit.id}. "
                    f"({marker.value} * {chosen.transit.value})."
                )
                return moves

        n += 1
    return moves


def run():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    grid = Grid.build()
    grid.mark(*grid.partition())
    pprint.pprint(vars(grid))

    moves = game(grid, limit=100000)
    logger.info(f"Game ends after {len(moves)} moves.")


if __name__ == "__main__":
    run()
