import {
  Box, Table, Thead, Tbody, Tr, Th, Td,
  Badge, Text, Flex, IconButton, Tooltip,
  Input, InputGroup, InputLeftElement, Button,
  Menu, MenuButton, MenuList, MenuItem
} from '@chakra-ui/react'
import { useEffect, useState } from 'react'
import api from '../services/api'
import { FiSearch, FiFilter, FiMoreHorizontal, FiMail, FiExternalLink, FiRefreshCw } from 'react-icons/fi'

const StatusBadge = ({ status }) => {
  const colors = {
    DISCOVERED: 'blue',
    ENRICHED: 'purple',
    CONTACTED: 'orange',
    INTERESTED: 'green',
    RESPONDED: 'cyan',
    REJECTED: 'red'
  }
  return (
    <Badge colorScheme={colors[status] || 'gray'} variant="solid" fontSize="xs" borderRadius="sm">
      {status}
    </Badge>
  )
}

const DealerPipeline = () => {
  const [dealers, setDealers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const fetchDealers = async () => {
    try {
      setLoading(true)
      const res = await api.get('/api/dealers?limit=100')
      setDealers(res.data)
    } catch (error) {
      console.error('Error fetching dealers:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDealers()
  }, [])

  const filteredDealers = dealers.filter(d =>
    d.business_name.toLowerCase().includes(search.toLowerCase()) ||
    d.city?.toLowerCase().includes(search.toLowerCase()) ||
    d.state?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <Box maxW="1600px" mx="auto">
      <Flex mb={6} justify="space-between" align="center">
        <Box>
          <Text fontSize="2xl" fontWeight="bold" color="white" letterSpacing="tight">
            Dealer Pipeline
          </Text>
          <Text color="dark.muted" fontSize="sm">
            Manage and track dealer outreach status
          </Text>
        </Box>
        <Flex gap={3}>
          <Button
            leftIcon={<FiRefreshCw />}
            variant="ghost"
            size="sm"
            onClick={fetchDealers}
            isLoading={loading}
          >
            Refresh
          </Button>
          <Button leftIcon={<FiFilter />} variant="outline" size="sm">
            Filter
          </Button>
          <Button colorScheme="brand" size="sm">
            Add Dealer
          </Button>
        </Flex>
      </Flex>

      <Box mb={6}>
        <InputGroup>
          <InputLeftElement pointerEvents="none">
            <FiSearch color="gray.500" />
          </InputLeftElement>
          <Input
            placeholder="Search dealers by name, city, or state..."
            bg="dark.card"
            border="1px solid"
            borderColor="dark.border"
            _focus={{ borderColor: 'brand.500', boxShadow: 'none' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </InputGroup>
      </Box>

      <Box
        bg="dark.card"
        borderRadius="lg"
        border="1px solid"
        borderColor="dark.border"
        overflow="hidden"
      >
        <Table variant="simple" size="sm">
          <Thead bg="rgba(255,255,255,0.02)">
            <Tr>
              <Th color="dark.muted">ID</Th>
              <Th color="dark.muted">Business Name</Th>
              <Th color="dark.muted">Location</Th>
              <Th color="dark.muted">Status</Th>
              <Th color="dark.muted">SOT Class</Th>
              <Th color="dark.muted">Contact</Th>
              <Th color="dark.muted" isNumeric>Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {filteredDealers.map((dealer) => (
              <Tr key={dealer.id} _hover={{ bg: 'dark.hover' }}>
                <Td fontFamily="mono" color="dark.muted">#{dealer.id}</Td>
                <Td>
                  <Text color="white" fontWeight="medium">{dealer.business_name}</Text>
                  {dealer.website && (
                    <Flex align="center" mt={1}>
                      <FiExternalLink size={10} color="#888" />
                      <Text as="a" href={dealer.website} target="_blank" fontSize="xs" color="brand.500" ml={1}>
                        {new URL(dealer.website).hostname}
                      </Text>
                    </Flex>
                  )}
                </Td>
                <Td>
                  <Text color="dark.text" fontSize="sm">{dealer.city}, {dealer.state}</Text>
                </Td>
                <Td>
                  <StatusBadge status={dealer.status} />
                </Td>
                <Td>
                  {dealer.sot_class === 'Class 3 SOT' ? (
                    <Badge colorScheme="purple" variant="outline" fontSize="xs">Class 3</Badge>
                  ) : (
                    <Text fontSize="xs" color="dark.muted">-</Text>
                  )}
                </Td>
                <Td>
                  <Flex gap={2}>
                    {dealer.email && (
                      <Tooltip label={dealer.email}>
                        <Badge colorScheme="blue" variant="subtle">EMAIL</Badge>
                      </Tooltip>
                    )}
                    {dealer.contact_form_url && (
                      <Tooltip label="Has Contact Form">
                        <Badge colorScheme="orange" variant="subtle">FORM</Badge>
                      </Tooltip>
                    )}
                  </Flex>
                </Td>
                <Td isNumeric>
                  <Menu>
                    <MenuButton
                      as={IconButton}
                      icon={<FiMoreHorizontal />}
                      variant="ghost"
                      size="sm"
                      aria-label="Options"
                    />
                    <MenuList bg="dark.card" borderColor="dark.border">
                      <MenuItem icon={<FiMail />} bg="transparent" _hover={{ bg: 'dark.hover' }}>
                        Send Outreach
                      </MenuItem>
                      <MenuItem icon={<FiExternalLink />} bg="transparent" _hover={{ bg: 'dark.hover' }}>
                        View Details
                      </MenuItem>
                    </MenuList>
                  </Menu>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
        {filteredDealers.length === 0 && (
          <Box p={8} textAlign="center">
            <Text color="dark.muted">No dealers found matching your search.</Text>
          </Box>
        )}
      </Box>
    </Box>
  )
}

export default DealerPipeline
