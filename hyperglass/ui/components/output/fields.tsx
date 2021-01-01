import { forwardRef } from 'react';
import { Icon, Text, Box, Tooltip, Menu, MenuButton, MenuList } from '@chakra-ui/react';
import { CgMoreO as More } from '@meronex/icons/cg';
import { BisError as Warning } from '@meronex/icons/bi';
import { MdNotInterested as NotAllowed } from '@meronex/icons/md';
import { RiHome2Fill as End } from '@meronex/icons/ri';
import { BsQuestionCircleFill as Question } from '@meronex/icons/bs';
import { FaCheckCircle as Check, FaChevronRight as ChevronRight } from '@meronex/icons/fa';
import dayjs from 'dayjs';
import relativeTimePlugin from 'dayjs/plugin/relativeTime';
import utcPlugin from 'dayjs/plugin/utc';
import { If } from '~/components';
import { useConfig, useColorValue } from '~/context';
import { useOpposingColor } from '~/hooks';

import type {
  TAge,
  TActive,
  TWeight,
  TASPath,
  TMonoField,
  TRPKIState,
  TCommunities,
} from './types';

dayjs.extend(relativeTimePlugin);
dayjs.extend(utcPlugin);

export const MonoField = (props: TMonoField) => {
  const { v, ...rest } = props;
  return (
    <Text as="span" fontSize="sm" fontFamily="mono" {...rest}>
      {v}
    </Text>
  );
};

export const Active = (props: TActive) => {
  const { isActive } = props;
  const color = useColorValue(['gray.500', 'green.500'], ['whiteAlpha.300', 'blackAlpha.500']);
  return (
    <>
      <If c={isActive}>
        <Icon color={color[+isActive]} as={Check} />
      </If>
      <If c={!isActive}>
        <Icon color={color[+isActive]} as={NotAllowed} />
      </If>
    </>
  );
};

export const Age = (props: TAge) => {
  const { inSeconds, ...rest } = props;
  const now = dayjs.utc();
  const then = now.subtract(inSeconds, 'second');
  return (
    <Tooltip hasArrow label={then.toString().replace('GMT', 'UTC')} placement="right">
      <Text fontSize="sm" {...rest}>
        {now.to(then, true)}
      </Text>
    </Tooltip>
  );
};

export const Weight = (props: TWeight) => {
  const { weight, winningWeight, ...rest } = props;
  const fixMeText =
    winningWeight === 'low' ? 'Lower Weight is Preferred' : 'Higher Weight is Preferred';
  return (
    <Tooltip hasArrow label={fixMeText} placement="right">
      <Text fontSize="sm" fontFamily="mono" {...rest}>
        {weight}
      </Text>
    </Tooltip>
  );
};

export const ASPath = (props: TASPath) => {
  const { path, active } = props;
  const color = useColorValue(
    // light: inactive, active
    ['blackAlpha.500', 'blackAlpha.500'],
    // dark: inactive, active
    ['whiteAlpha.600', 'blackAlpha.700'],
  );

  if (path.length === 0) {
    return <Icon as={End} />;
  }

  let paths = [] as JSX.Element[];

  path.map((asn, i) => {
    const asnStr = String(asn);
    i !== 0 &&
      paths.push(
        <Icon as={ChevronRight} key={`separator-${i}`} color={color[+active]} boxSize={5} px={2} />,
      );
    paths.push(
      <Text fontSize="sm" as="span" whiteSpace="pre" fontFamily="mono" key={`as-${asnStr}-${i}`}>
        {asnStr}
      </Text>,
    );
  });

  return <>{paths}</>;
};

export const Communities = (props: TCommunities) => {
  const { communities } = props;
  const bg = useColorValue('white', 'gray.900');
  const color = useOpposingColor(bg);
  return (
    <>
      <If c={communities.length === 0}>
        <Tooltip placement="right" hasArrow label="No Communities">
          <Icon as={Question} />
        </Tooltip>
      </If>
      <If c={communities.length !== 0}>
        <Menu>
          <MenuButton>
            <Icon as={More} />
          </MenuButton>
          <MenuList
            p={3}
            bg={bg}
            width="unset"
            color={color}
            textAlign="left"
            fontFamily="mono"
            fontWeight="normal"
            whiteSpace="pre-wrap">
            {communities.join('\n')}
          </MenuList>
        </Menu>
      </If>
    </>
  );
};

export const RPKIState = forwardRef<HTMLDivElement, TRPKIState>((props, ref) => {
  const { state, active } = props;
  const { web } = useConfig();
  const bg = useColorValue(
    [
      ['red.400', 'green.500', 'yellow.400', 'gray.500'],
      ['red.500', 'green.500', 'yellow.500', 'gray.600'],
    ],
    [
      ['red.300', 'green.300', 'yellow.300', 'gray.300'],
      ['red.500', 'green.600', 'yellow.500', 'gray.800'],
    ],
  );
  const color = useOpposingColor(bg[+active][state]);
  const icon = [NotAllowed, Check, Warning, Question];

  const text = [
    web.text.rpki_invalid,
    web.text.rpki_valid,
    web.text.rpki_unknown,
    web.text.rpki_unverified,
  ];

  return (
    <Tooltip
      hasArrow
      placement="right"
      label={text[state] ?? text[3]}
      bg={bg[+active][state]}
      color={color}>
      <Box ref={ref} boxSize={5}>
        <Box as={icon[state]} color={bg[+active][state]} />
      </Box>
    </Tooltip>
  );
});
