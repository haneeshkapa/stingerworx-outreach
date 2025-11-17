import { Box, Flex, Heading, Button, HStack, Text } from '@chakra-ui/react'
import { Link as RouterLink } from 'react-router-dom'

export default function Navbar() {
  return (
    <Box bg="white" px={8} py={4} shadow="sm" borderBottom="1px" borderColor="gray.200">
      <Flex justify="space-between" align="center" maxW="1400px" mx="auto">
        <HStack spacing={8}>
          <Heading size="md" color="brand.600">
            🎯 Stingerworx Outreach
          </Heading>
          <HStack spacing={4}>
            <Button as={RouterLink} to="/" variant="ghost" colorScheme="brand">
              Dashboard
            </Button>
            <Button as={RouterLink} to="/dealers" variant="ghost" colorScheme="brand">
              Dealers
            </Button>
            <Button as={RouterLink} to="/campaigns" variant="ghost" colorScheme="brand">
              Campaigns
            </Button>
            <Button as={RouterLink} to="/logs" variant="ghost" colorScheme="brand">
              Logs
            </Button>
          </HStack>
        </HStack>
        <Text fontSize="sm" color="gray.600">
          Tenant: Stingerworx
        </Text>
      </Flex>
    </Box>
  )
}
