import { IconButton } from '@chakra-ui/react';

import type { TTableIconButton } from './types';

export const TableIconButton = (props: TTableIconButton): JSX.Element => (
  <IconButton size="sm" borderWidth={1} {...props} aria-label="Table Icon Button" />
);
