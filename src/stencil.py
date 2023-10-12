"""Main class for calculating estimated daily price."""
import dataclasses
from asyncio import create_task, gather
from typing import Dict, List, Literal, Tuple

from src.bins import PriceBins
from src.logger import init_logger

logger = init_logger("bitcoin_price_oracle")


@dataclasses.dataclass
class StencilValues:
    """Dataclass representing the stencil values for the Stencil class."""

    values: Dict[int, float]
    round_usd_stencil: List[float]


@dataclasses.dataclass
class Bounds:
    """Dataclass representing the bounds for the Stencil class."""

    lower_bound: int
    upper_bound: int
    btc_bound: int


@dataclasses.dataclass
class BitcoinDailyPriceValues:
    """Dataclass representing the values from the BitcoinDailyPrice class."""

    number_of_bins: int
    output_bell_curve_bins: List[int]
    output_bell_curve_bin_counts: List[int]


class Stencil:
    """
    Stencil class for calculating estimated daily price.

    This class implements the stencil algorithm to estimate Bitcoin prices
    based on specified parameters.
    """

    min_slide: int = -200
    max_slide: int = 200
    total_score: float = 0.0
    number_of_scores: int = 0
    best_slide_score: float = 0.0
    best_slide: int = 0

    bounds: Bounds
    values: StencilValues

    bitcoin_daily_price_values: BitcoinDailyPriceValues

    def __init__(
        self,
        bins: PriceBins,
    ):
        """
        Initialize the Stencil object.

        This method initializes the Stencil object with specified
        price bins. It sets up scores for sliding the stencil and defines
        bounds for the curve.

        :param bins: PriceBins object containing information about price bins.
        :type bins: PriceBins
        """
        self.bounds = Bounds(
            lower_bound=bins.lower_bound, upper_bound=bins.upper_bound, btc_bound=1401
        )

        self.stencil_values = StencilValues(
            values={
                401: 0.0005957955691168063,  # $1
                402: 0.0004454790662303128,  # (next one for tx/atm fees)
                429: 0.0001763099393598914,  # $1.50
                430: 0.0001851801497144573,
                461: 0.0006205616481885794,  # $2
                462: 0.0005985696860584984,
                496: 0.0006919505728046619,  # $3
                497: 0.0008912933078342840,
                540: 0.0009372916238804205,  # $5
                541: 0.0017125522985034724,  # (larger needed range for fees)
                600: 0.0021702347223143030,
                601: 0.0037018622326411380,  # $10
                602: 0.0027322168706743802,
                603: 0.0016268322583097678,  # (larger needed range for fees)
                604: 0.0012601953416497664,
                661: 0.0041425242880295460,  # $20
                662: 0.0039247767475640830,
                696: 0.0032399441632017228,  # $30
                697: 0.0037112959007355585,
                740: 0.0049921908828370000,  # $50
                741: 0.0070636869018197105,
                801: 0.0080000000000000000,  # $100
                802: 0.0065431388282424440,  # (larger needed range for fees)
                803: 0.0044279509203361735,
                861: 0.0046132440551747015,  # $200
                862: 0.0043647851395531140,
                896: 0.0031980892880846567,  # $300
                897: 0.0034237641632481910,
                939: 0.0025995335505435034,  # $500
                940: 0.0032631930982226645,  # (larger needed range for fees)
                941: 0.0042753262790881080,
                1001: 0.0037699501474772350,  # $1,000
                1002: 0.0030872891064215764,  # (larger needed range for fees)
                1003: 0.0023237040836798163,
                1061: 0.0023671764210889895,  # $2,000
                1062: 0.0020106877104798474,
                1140: 0.0009099214128654502,  # $3,000
                1141: 0.0012008546799361498,
                1201: 0.0007862586076341524,  # $10,000
                1202: 0.0006900048077192579,
            },
            round_usd_stencil=[0.0] * bins.number_of_bins,
        )

        self.bitcoin_daily_price_values = BitcoinDailyPriceValues(
            number_of_bins=bins.number_of_bins,
            output_bell_curve_bins=bins.output_bell_curve_bins,
            output_bell_curve_bin_counts=bins.output_bell_curve_bin_counts,
        )

    async def run_stencil(self) -> int:
        """
        Run the stencil algorithm to estimate the BTC price.

        This method executes the steps of the stencil algorithm to
        estimate the BTC price. It populates the stencil, finds the
        best slide, calculates neighbor scores, calculates the price
        estimate, and logs the estimate.

        :return: Estimated BTC price in USD
        :rtype: int
        """
        logger.info("Running stencil...")
        self._populate_stencil()

        scores = await gather(
            *[
                create_task(self._find_best_slide()),
                create_task(self._get_neighbor_scores()),
            ]
        )

        price_estimate = self._calculate_price_estimate(
            scores[0], scores[1][0], scores[1][1]
        )
        logger.info(
            "The btc price estimate is: $%s",
            f"{price_estimate:,}",
        )
        return price_estimate

    def _populate_stencil(self):
        """
        Populate the round USD stencil with specified values.

        This method populates the round USD stencil with predefined
        values at specific indices.
        """
        for index, value in self.stencil_values.values.items():
            self.stencil_values.round_usd_stencil[index] = value

    async def _find_best_slide(self) -> float:
        """
        Find the best slide for the curve to maximize the slide score.

        This method iterates through the specified range of slides,
        calculates slide scores, and updates the best slide and its
        score accordingly.

        :return: The estimated USD price for the best slide.
        :rtype: float
        """
        for slide in range(self.min_slide, self.max_slide):
            slide_score = self._calculate_slide_score(slide)
            self.total_score += slide_score
            self.number_of_scores += 1

            if slide_score > self.best_slide_score:
                self.best_slide_score = slide_score
                self.best_slide = slide

        # estimate the usd price of the best slide
        usd100_in_btc_best = self.bitcoin_daily_price_values.output_bell_curve_bins[
            801 + self.best_slide
        ]
        btc_in_usd_best = 100 / (usd100_in_btc_best)

        return btc_in_usd_best

    def _calculate_slide_score(self, slide: int) -> float:
        """
        Calculate the slide score for a given slide value.

        This method calculates the slide score by shifting the curve and
        multiplying the shifted curve with the round USD stencil, summing
        the product.

        :param slide: The slide value for shifting the curve.
        :type slide: int

        :return: The calculated slide score.
        :rtype: float
        """
        shifted_curve = self.bitcoin_daily_price_values.output_bell_curve_bin_counts[
            self.bounds.lower_bound + slide : self.bounds.btc_bound + slide
        ]
        slide_score = sum(
            curve * self.stencil_values.round_usd_stencil[n + self.bounds.lower_bound]
            for n, curve in enumerate(shifted_curve)
        )
        return slide_score

    async def _get_neighbor_scores(self) -> Tuple[float, int]:
        """
        Get the scores of the neighboring slides.

        This method calculates the scores of the neighboring slides (up and down),
        determines the best neighbor based on the higher score, and computes the
        USD price estimation for the best neighbor.

        :return: A tuple containing the score of the best neighbor and its USD price.
        :rtype: tuple[float, float]
        """
        # Find best slide neighbor (either up or down)
        scores = await gather(
            *[
                create_task(self._calculate_neighbor_score("up")),
                create_task(self._calculate_neighbor_score("down")),
            ]
        )

        # Determine the best neighbor
        neighbor_score = scores[0] if scores[0] > scores[1] else scores[1]

        # get best neighbor usd price
        usd100_in_btc_2nd = self.bitcoin_daily_price_values.output_bell_curve_bins[
            801 + self.best_slide + (1 if scores[0] > scores[1] else -1)
        ]

        btc_in_usd_2nd = 100 / (usd100_in_btc_2nd)

        return neighbor_score, btc_in_usd_2nd

    async def _calculate_neighbor_score(
        self, direction: Literal["up", "down"]
    ) -> float:
        """
        Calculate the score of the neighboring slide in the specified direction.

        :param direction: The direction to calculate the neighboring slide score.
            Should be either "up" or "down".
        :type direction: Literal["up", "down"]

        :return: The calculated score of the neighboring slide.
        :rtype: float
        """
        slide_change = {"up": 1, "down": -1}.get(direction, 0)
        slide = self.best_slide + slide_change
        neighbor_curve = self.bitcoin_daily_price_values.output_bell_curve_bin_counts[
            self.bounds.lower_bound + slide : self.bounds.btc_bound + slide
        ]
        neighbor_score = sum(
            neighbor_curve[n]
            * self.stencil_values.round_usd_stencil[n + self.bounds.lower_bound]
            for n in range(len(neighbor_curve))
        )
        return neighbor_score

    def _calculate_price_estimate(
        self, btc_in_usd_best: float, neighbor_score: float, btc_in_usd_2nd: float
    ) -> int:
        """
        Calculate the price estimate.

        This method calculates the price estimate based on the average
        score, differences between the best slide's score and the average
        score, and the neighbor's score and the average score. It then
        calculates weights based on these differences and computes the price
        estimate.

        :param btc_in_usd_best: The estimated btc USD value for the best slide.
        :type btc_in_usd_best: float
        :param neighbor_score: The score of the neighboring slide.
        :type neighbor_score: float
        :param btc_in_usd_2nd: The estimated btc USD value for the second best slide.
        :type btc_in_usd_2nd: float

        :return: The calculated price estimate.
        :rtype: int
        """
        # Calculate average score and differences
        avg_score = self.total_score / self.number_of_scores
        a1 = self.best_slide_score - avg_score
        a2 = abs(neighbor_score - avg_score)  # Theoretically possible to be negative

        # Calculate weights
        total_a = a1 + a2
        w1 = a1 / total_a
        w2 = a2 / total_a

        # Calculate the price estimate
        price_estimate = int(w1 * btc_in_usd_best + w2 * btc_in_usd_2nd)

        return price_estimate
